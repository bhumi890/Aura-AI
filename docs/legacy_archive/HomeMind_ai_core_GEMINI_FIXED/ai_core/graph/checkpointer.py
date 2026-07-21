"""
ai_core/graph/checkpointer.py

Checkpointer backend selection -- Postgres in production, SQLite in
development, both keyed on thread_id (== session_id). Isolated here so
swapping checkpoint backends never touches graph topology.

IMPORTANT -- async context manager pitfall:
`AsyncSqliteSaver.from_conn_string(...)` and `AsyncPostgresSaver.from_conn_string(...)`
are decorated with `@asynccontextmanager`. Calling them does NOT return a
saver -- it returns an `_AsyncGeneratorContextManager` that *yields* the
saver on `__aenter__`. Returning that context manager directly (instead
of the saver) is what previously caused:

    AttributeError: '_AsyncGeneratorContextManager' object has no
    attribute 'get_next_version'

...because `graph.compile(checkpointer=...)` was handed the wrapper
object instead of a real BaseCheckpointSaver.

We can't use `async with ... as checkpointer:` here and return
`checkpointer` from inside the block, because the connection would be
closed the instant the block exits -- and `build_app()` (per the
project's public runtime API) must return a graph that stays usable for
the lifetime of the process, not just for one `with` block. So instead
we enter the context manager manually via `__aenter__()` and keep the
connection open for the app's lifetime. `_open_checkpointer_cms` keeps a
reference to each context manager so it can be cleanly closed via
`close_checkpointers()` on shutdown, if the caller chooses to do so --
this is optional and does not change the existing `build_app()` API.
"""
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ai_core.config import ENV, POSTGRES_CONN_STRING, SQLITE_DB_PATH

# Keeps references to opened context managers so their connections can be
# closed on graceful shutdown. Not required for build_app() to work, but
# avoids leaking connections if the caller wants to clean up explicitly.
_open_checkpointer_cms = []


async def get_checkpointer():
    if ENV == "production":
        cm = AsyncPostgresSaver.from_conn_string(POSTGRES_CONN_STRING)
        checkpointer = await cm.__aenter__()  # actual AsyncPostgresSaver, not the cm
        _open_checkpointer_cms.append(cm)
        await checkpointer.setup()  # creates tables on first run, no-op after
        return checkpointer
    else:
        cm = AsyncSqliteSaver.from_conn_string(SQLITE_DB_PATH)
        checkpointer = await cm.__aenter__()  # actual AsyncSqliteSaver, not the cm
        _open_checkpointer_cms.append(cm)
        return checkpointer


async def close_checkpointers():
    """Optional graceful shutdown hook -- closes any checkpointer connections
    opened via get_checkpointer(). Not called automatically; wire it into
    your app's shutdown lifecycle (e.g. FastAPI's shutdown event) if desired.
    """
    while _open_checkpointer_cms:
        cm = _open_checkpointer_cms.pop()
        await cm.__aexit__(None, None, None)

"""
Convenience entrypoint for running the Knowledge Agent's tests directly
from this package, as specified in the project folder structure.

The actual pytest test cases live under `tests/unit/` and
`tests/integration/` (standard pytest discovery layout). This module lets
you run:

    python -m pytest ai_core/agents/knowledge/tests.py

which collects and runs the Knowledge Agent-specific test modules.
"""

from __future__ import annotations

pytest_plugins: list[str] = []

collect_ignore_glob: list[str] = []

# Re-export so `pytest ai_core/agents/knowledge/tests.py` collects the same
# test cases as `pytest tests/unit/test_knowledge_agent.py`.
from tests.unit.test_knowledge_agent import *  # noqa: F401,F403,E402

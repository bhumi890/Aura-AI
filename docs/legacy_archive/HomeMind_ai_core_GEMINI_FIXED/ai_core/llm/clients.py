"""
ai_core/llm/clients.py

Instantiates the actual LLM client objects. Model choice and API config
live in exactly one place -- if a new model tier ships, this is the only
file that changes.

Root cause note (July 2026): calls started failing with
    404 NotFound: This model models/gemini-2.5-flash-lite is not available
Google has been retiring Gemini 2.5 Flash / Flash-Lite ahead of their
published Oct 16 2026 shutdown date -- 404s on those model IDs started
appearing in early July 2026, independent of API key validity or SDK
version (confirmed via Google's own Gemini API forum and deprecations
page). The fix is NOT a newer client library -- it's to stop pointing at
a model Google is actively sunsetting. See llm/models.py for the current
model choices. We stay on langchain-google-genai's 2.x line (see
requirements.txt) since 4.x requires langchain-core>=1.2.5, which is
incompatible with the pinned langgraph==0.2.74 / langgraph-checkpoint
stack this project already has working.
"""
from functools import lru_cache
from typing import Any, List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from ai_core.llm.models import FAST_MODEL, SYNTHESIS_MODEL


def _ensure_human_turn(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Gemini's API rejects a request whose `contents` end up empty -- which
    happens whenever the message list passed to the model is a single
    SystemMessage with nothing else. That shape was valid for Anthropic
    (system + no turns is fine) but several nodes in this project build
    their prompt that way (supervisor_entry, emotion_node, memory_agent,
    wellness_plan_node). Rather than touching every call site, we patch
    it once here: if no human/ai turn is present, append a minimal
    placeholder human turn so Gemini has a non-system message to answer.
    """
    if any(not isinstance(m, SystemMessage) for m in messages):
        return messages
    return list(messages) + [HumanMessage(content="Continue.")]


def _reraise_with_model_hint(exc: Exception, model: str):
    """
    Google's 404 for a retired/unavailable model is easy to misdiagnose as
    a library or auth bug (see module docstring). If that's what just
    happened, re-raise with a pointer to where the model name actually
    lives, instead of leaving the caller to rediscover this the hard way.
    """
    message = str(exc)
    if "404" in message and ("not available" in message.lower() or "not found" in message.lower()):
        raise RuntimeError(
            f"Gemini model '{model}' was rejected by the API (404). This model may "
            "have been retired or is not enabled for this API key -- it is not "
            "necessarily a library/config bug. Check Google's Gemini deprecations "
            "page, update FAST_MODEL / SYNTHESIS_MODEL in ai_core/config.py and "
            "ai_core/llm/models.py to a currently-supported model, and re-run."
        ) from exc
    raise exc


class GeminiChatModel(ChatGoogleGenerativeAI):
    """
    Thin wrapper around ChatGoogleGenerativeAI that patches the
    system-message-only request shape used throughout ai_core's agent
    nodes (see `_ensure_human_turn`), and adds a clearer error message
    when Google rejects the configured model outright (see
    `_reraise_with_model_hint`). The patch is applied at the
    _generate/_agenerate level -- not invoke/ainvoke -- so it still
    applies when this model is wrapped by `.with_structured_output(...)`,
    since that wrapper (bind_tools + parser) ultimately calls back into
    these same generate methods on the bound model instance.
    """

    def _generate(self, messages: List[BaseMessage], *args: Any, **kwargs: Any):
        try:
            return super()._generate(_ensure_human_turn(messages), *args, **kwargs)
        except Exception as exc:
            _reraise_with_model_hint(exc, self.model)

    async def _agenerate(self, messages: List[BaseMessage], *args: Any, **kwargs: Any):
        try:
            return await super()._agenerate(_ensure_human_turn(messages), *args, **kwargs)
        except Exception as exc:
            _reraise_with_model_hint(exc, self.model)


@lru_cache(maxsize=1)
def get_fast_llm() -> GeminiChatModel:
    """Used by: supervisor_entry, emotion_node, memory_agent, wellness_plan_node."""
    return GeminiChatModel(model=FAST_MODEL, temperature=0)


@lru_cache(maxsize=1)
def get_synthesis_llm() -> GeminiChatModel:
    
    return GeminiChatModel(
        model=SYNTHESIS_MODEL,
        temperature=0.4,
       
    )
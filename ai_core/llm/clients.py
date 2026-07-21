"""
ai_core/llm/clients.py

Instantiates the actual LLM client objects using Groq (ChatGroq).
Model choice and API config live in exactly one place.
"""
from functools import lru_cache
from typing import Any, List
import os
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from ai_core.llm.models import FAST_MODEL, SYNTHESIS_MODEL


def _ensure_human_turn(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Ensures a request does not contain only SystemMessage with no human turn.
    """
    if any(not isinstance(m, SystemMessage) for m in messages):
        return messages
    return list(messages) + [HumanMessage(content="Continue.")]


def _reraise_with_model_hint(exc: Exception, model: str):
    message = str(exc)
    if "404" in message and ("not available" in message.lower() or "not found" in message.lower()):
        raise RuntimeError(
            f"Groq model '{model}' was rejected by the API (404/Not Found). Please check "
            "ai_core/llm/models.py for valid Groq model IDs (e.g. llama-3.1-8b-instant)."
        ) from exc
    raise exc


def _get_all_api_keys() -> List[str]:
    load_dotenv()
    keys = [
        os.environ.get("GROQ_API_KEY"),
        os.environ.get("GROQ_API_KEY_2"),
        os.environ.get("GROQ_API_KEY_3"),
        os.environ.get("GROQ_API_KEY_4"),
    ]
    return [k for k in keys if k and k.strip()]


class KeyPoolGroqChatModel(ChatGroq):
    """
    Auto-rotating multi-key Groq wrapper.
    Starts with a primary API key from the pool based on `primary_key_index`.
    If that key hits rate limits (429) or quota errors, automatically
    rotates through the other keys in the pool and retries immediately.
    """
    primary_key_index: int = 0

    def _get_client_for_key(self, api_key: str) -> ChatGroq:
        return ChatGroq(
            model_name=self.model_name,
            temperature=self.temperature,
            max_retries=1,
            api_key=api_key
        )

    def _invoke_with_fallback(self, func_name: str, messages: List[BaseMessage], *args: Any, **kwargs: Any):
        keys = _get_all_api_keys()
        if not keys:
            raise ValueError("No Groq API keys found in environment variables (GROQ_API_KEY).")

        last_exc = None
        for offset in range(len(keys)):
            key_idx = (self.primary_key_index + offset) % len(keys)
            current_key = keys[key_idx]
            try:
                client = self._get_client_for_key(current_key)
                func = getattr(client, func_name)
                return func(_ensure_human_turn(messages), *args, **kwargs)
            except Exception as exc:
                message = str(exc)
                if "429" in message or "RESOURCE_EXHAUSTED" in message or "Rate limit" in message or "Quota exceeded" in message:
                    last_exc = exc
                    continue
                _reraise_with_model_hint(exc, getattr(self, "model_name", "groq-model"))

        if last_exc:
            _reraise_with_model_hint(last_exc, getattr(self, "model_name", "groq-model"))
        raise RuntimeError("Unexpected error in KeyPoolGroqChatModel fallback loop.")

    async def _ainvoke_with_fallback(self, func_name: str, messages: List[BaseMessage], *args: Any, **kwargs: Any):
        keys = _get_all_api_keys()
        if not keys:
            raise ValueError("No Groq API keys found in environment variables (GROQ_API_KEY).")

        last_exc = None
        for offset in range(len(keys)):
            key_idx = (self.primary_key_index + offset) % len(keys)
            current_key = keys[key_idx]
            try:
                client = self._get_client_for_key(current_key)
                func = getattr(client, func_name)
                return await func(_ensure_human_turn(messages), *args, **kwargs)
            except Exception as exc:
                message = str(exc)
                if "429" in message or "RESOURCE_EXHAUSTED" in message or "Rate limit" in message or "Quota exceeded" in message:
                    last_exc = exc
                    continue
                _reraise_with_model_hint(exc, getattr(self, "model_name", "groq-model"))

        if last_exc:
            _reraise_with_model_hint(last_exc, getattr(self, "model_name", "groq-model"))
        raise RuntimeError("Unexpected error in KeyPoolGroqChatModel fallback loop.")

    def _generate(self, messages: List[BaseMessage], *args: Any, **kwargs: Any):
        return self._invoke_with_fallback("_generate", messages, *args, **kwargs)

    async def _agenerate(self, messages: List[BaseMessage], *args: Any, **kwargs: Any):
        return await self._ainvoke_with_fallback("_agenerate", messages, *args, **kwargs)


@lru_cache(maxsize=1)
def get_supervisor_llm() -> KeyPoolGroqChatModel:
    """Primary: Key 1 (Index 0). Used by supervisor_entry."""
    keys = _get_all_api_keys()
    return KeyPoolGroqChatModel(model_name=FAST_MODEL, temperature=0, primary_key_index=0, api_key=keys[0] if keys else "gsk_placeholder")


@lru_cache(maxsize=1)
def get_emotion_llm() -> KeyPoolGroqChatModel:
    """Primary: Key 2 (Index 1). Used by emotion_node."""
    keys = _get_all_api_keys()
    idx = 1 if len(keys) > 1 else 0
    return KeyPoolGroqChatModel(model_name=FAST_MODEL, temperature=0, primary_key_index=idx, api_key=keys[idx] if keys else "gsk_placeholder")


@lru_cache(maxsize=1)
def get_memory_llm() -> KeyPoolGroqChatModel:
    """Primary: Key 3 (Index 2). Used by memory_agent."""
    keys = _get_all_api_keys()
    idx = 2 if len(keys) > 2 else 0
    return KeyPoolGroqChatModel(model_name=FAST_MODEL, temperature=0, primary_key_index=idx, api_key=keys[idx] if keys else "gsk_placeholder")


@lru_cache(maxsize=1)
def get_wellness_llm() -> KeyPoolGroqChatModel:
    """Primary: Key 4 (Index 3). Used by wellness_plan_node."""
    keys = _get_all_api_keys()
    idx = 3 if len(keys) > 3 else 0
    return KeyPoolGroqChatModel(model_name=FAST_MODEL, temperature=0, primary_key_index=idx, api_key=keys[idx] if keys else "gsk_placeholder")


@lru_cache(maxsize=1)
def get_fast_llm() -> KeyPoolGroqChatModel:
    """Fallback / generic fast LLM."""
    return get_supervisor_llm()


@lru_cache(maxsize=1)
def get_synthesis_llm() -> KeyPoolGroqChatModel:
    """Primary: Key 1 (Index 0) or rotates through all 4. Used by supervisor_final."""
    keys = _get_all_api_keys()
    return KeyPoolGroqChatModel(
        model_name=SYNTHESIS_MODEL,
        temperature=0.4,
        primary_key_index=0,
        api_key=keys[0] if keys else "gsk_placeholder",
    )
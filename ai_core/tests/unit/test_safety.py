"""
ai_core/tests/unit/test_safety.py

Unit tests for deterministic safety classification and crisis resource formatting.
"""
import pytest
from ai_core.agents.safety.rules import classify_safety
from ai_core.agents.safety.resources import get_crisis_resources, format_crisis_message
from ai_core.agents.safety.node import crisis_response_node
from ai_core.state.schema import WellnessState


def test_classify_safety_suicide():
    assert classify_safety("I want to kill myself") == "crisis"
    assert classify_safety("thinking about hurting myself") == "at_risk"
    assert classify_safety("Hello, how are you today?") == "safe"


def test_classify_safety_misspellings_and_typos():
    # Various suicide misspellings
    assert classify_safety("i want to commit sucide") == "crisis"
    assert classify_safety("thinking of sewicide") == "crisis"
    assert classify_safety("i am feeling suicidial today") == "crisis"
    assert classify_safety("commit sui cide") == "crisis"
    assert classify_safety("i want to commit suic") == "crisis"
    assert classify_safety("suiside") == "crisis"
    assert classify_safety("siucide") == "crisis"
    
    # Other crisis misspellings
    assert classify_safety("i want to kil myself") == "crisis"
    assert classify_safety("i am gonna ovrdose") == "crisis"
    assert classify_safety("wana die right now") == "crisis"
    
    # At-risk misspellings
    assert classify_safety("struggling with selfharm") == "at_risk"
    assert classify_safety("cuting myself lately") == "at_risk"
    assert classify_safety("feel so hopless and worthless") == "at_risk"
    
    # Safe false positives
    assert classify_safety("i hope the swelling will subside soon") == "safe"
    assert classify_safety("we need to decide and succeed together") == "safe"


def test_get_crisis_resources():
    res = get_crisis_resources("suicide_and_self_harm")
    assert len(res) >= 1
    assert any(r["number"] == "9152987821" for r in res)


@pytest.mark.asyncio
async def test_crisis_response_node():
    state: WellnessState = {"user_message": "I want to end my life", "session_id": "test_123"}
    out = await crisis_response_node(state)
    assert "9152987821" in out["final_response"]
    assert out["metadata"]["crisis_path_triggered"] is True

"""
ai_core/agents/safety/rules.py

Rule-based, deterministic crisis/risk detection. This is deliberately NOT
an LLM call -- per the Part 1 design, safety routing must be auditable and
not dependent on probabilistic model output. This module is the one place
the team's safety owner (M5) should extend with additional detection logic,
severity scoring, or escalation rules.

Kept separate from node.py so the detection rules can be unit-tested in
isolation from the LangGraph node wrapper.
"""
import re
from typing import Literal

SafetyStatus = Literal["safe", "at_risk", "crisis", "unknown"]

# ---------------------------------------------------------------------------
# NOTE ON OWNERSHIP: this is a first-pass, maintained baseline for the
# mandatory safety gate -- NOT a clinical instrument. The M5 safety team
# should treat this as a starting point to review, extend, and tune against
# real (de-identified) traffic and known false-negative/positive cases
# before this is relied on in production. In particular:
#   - Pattern lists are necessarily incomplete (they can't cover every
#     phrasing, language, or indirect/coded expression of risk).
#   - Thresholds here are binary (any match = flagged); severity scoring,
#     multi-turn context (e.g. escalating risk across a session), and
#     negation handling ("I'm NOT thinking about hurting myself") are
#     intentionally left as future extensions rather than guessed at here.
#   - This stays deterministic/rule-based by design (see module docstring)
#     so the mandatory gate is auditable; do not swap this for an LLM call
#     without sign-off, per the Part 1 design.
# ---------------------------------------------------------------------------

# Crisis: explicit statements of active suicidal/self-harm intent, a plan,
# means, or an imminent act. Anything matching here short-circuits straight
# to crisis_response_node (see graph/edges.py::route_after_safety).
_CRISIS_PATTERNS: list[str] = [
    r"\bkill (myself|me)\b",
    r"\bsuicid(e|al)\b",
    r"\bend(ing)? my (own )?life\b",
    r"\bwant(ing)? to die\b",
    r"\bdon'?t want to (be alive|live anymore|exist anymore)\b",
    r"\btake my (own )?life\b",
    r"\bno reason to (live|keep living)\b",
    r"\bbetter off dead\b",
    r"\bgoing to (kill myself|end it|end my life)\b",
    r"\bplan(ning)? to (kill myself|end my life|hurt myself)\b",
    r"\bhave (a plan|the pills|a gun) to\b",
    r"\bthis is (my )?(goodbye|suicide note)\b",
    r"\bwish i (was|were) dead\b",
    r"\bwant to (overdose|od)\b",
]

# At-risk: hopelessness, passive ideation, disclosed self-harm behavior, or
# distress that warrants a gentler/more cautious response and closer
# monitoring, but doesn't indicate an imminent act. Does NOT short-circuit
# the graph -- flows through normally so downstream nodes (emotion, memory,
# final synthesis) can shape a supportive response around it.
_AT_RISK_PATTERNS: list[str] = [
    r"\bself[\s-]?harm\b",
    r"\bcutting myself\b",
    r"\bhurt(ing)? myself\b",
    r"\bcan'?t (go on|do this anymore|take it anymore)\b",
    r"\bfeel(ing)? hopeless\b",
    r"\bno point in (living|anything|trying)\b",
    r"\bwant to disappear\b",
    r"\bfeel(ing)? like a burden\b",
    r"\bwhat'?s the point (of|in) (living|anything)\b",
    r"\bi'?m (a )?(worthless|useless)\b",
    r"\bnobody would (miss|care if) (i'?m gone|i died)\b",
    r"\bthinking about (hurting|harming) myself\b",
]

_CRISIS_RE = [re.compile(p) for p in _CRISIS_PATTERNS]
_AT_RISK_RE = [re.compile(p) for p in _AT_RISK_PATTERNS]


def _normalize(text: str) -> str:
    """Lowercase and collapse whitespace/punctuation noise so patterns match
    reliably against casual, typo-prone chat input."""
    text = text.lower()
    text = re.sub(r"[^\w\s']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def classify_safety(user_message: str) -> SafetyStatus:
    """
    Deterministic classification of a single user message.

    Returns "unknown" only for missing/unparseable input -- every real
    message resolves to "safe", "at_risk", or "crisis". This function is
    the single integration point the rest of the graph depends on; keep
    its signature stable even as the detection rules evolve.
    """
    if not user_message or not user_message.strip():
        return "unknown"

    text = _normalize(user_message)

    if any(pattern.search(text) for pattern in _CRISIS_RE):
        return "crisis"
    if any(pattern.search(text) for pattern in _AT_RISK_RE):
        return "at_risk"
    return "safe"

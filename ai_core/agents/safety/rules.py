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
    r"\b(want|wanna|gonna|going to|trying to) die\b",
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
    # Broader intent phrases that don't rely on correct spelling
    r"\b(want|wanna|thinking of|considering|planning) (to )?(end|take) (it|my life|everything)\b",
    r"\blife (is|isn'?t) worth (living|it)\b",
    r"\b(i'?m|i am) (going to|gonna) (end|kill|hurt) (myself|my life)\b",
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

# ---------------------------------------------------------------------------
# Fuzzy suicide keyword matcher: covers common chat typos and misspellings
# (e.g. "sucide", "suicde", "suicied", "suiside") that exact regex can't catch.
# Uses Levenshtein edit distance <= 2 on individual tokens (>= 5 chars).
# This is intentionally the ONLY fuzzy logic in the safety gate -- the cost
# of a false-negative (missed crisis) outweighs a false-positive here.
# ---------------------------------------------------------------------------
_SUICIDE_TARGETS = ("suicide", "suicidal", "suicidally", "suicided", "suiciding")

_SUICIDE_REGEXES = [
    re.compile(r"\b(s[uewyi]+[i]?|siu)\s*[cszk]\s*[i]?\s*[d]\s*[eaiylm]*\b"),
    re.compile(r"\b(suic|sucid|suis|suid|siuc|suii)\b"),
    re.compile(r"\bsui\s+(cide|side|cid|sid|cde)\b"),
]

_SAFE_SUICIDE_FALSE_POSITIVES = {
    "subside",
    "subsides",
    "subsided",
    "subsiding",
    "succeed",
    "succeeds",
    "succeeded",
    "secede",
    "seceded",
    "decide",
    "decides",
    "decided",
    "reside",
    "resides",
    "resided",
    "beside",
    "besides",
    "inside",
    "guide",
    "guides",
    "guided",
    "lucid",
    "provide",
    "provides",
    "provided",
    "juice",
    "juices",
    "juiced",
    "sublime",
    "suitcase",
    "suitcases",
    "suite",
    "suites",
    "suitor",
    "suitors",
    "suitable",
    "suit",
    "suits",
    "suited",
    "sushi",
    "sued",
    "suds",
    "scud",
    "stud",
    "side",
    "slide",
}


def _levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(a) < len(b):
        return _levenshtein(b, a)
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def _fuzzy_suicide_match(text: str) -> bool:
    """
    True if any token in text matches suicide regex patterns or is within
    Levenshtein edit distance of a suicide keyword.
    Catches: sucide, suicde, suicied, suiside, suicidel, sewicide, siucide, etc.
    While safely excluding words like subside, succeed, secede, decide.
    """
    for reg in _SUICIDE_REGEXES:
        for match in reg.finditer(text):
            word = match.group(0).replace(" ", "")
            if word not in _SAFE_SUICIDE_FALSE_POSITIVES:
                return True

    for token in text.split():
        if token in _SAFE_SUICIDE_FALSE_POSITIVES:
            continue
        if len(token) == 4 and _levenshtein(token, "suic") <= 1:
            return True
        if 5 <= len(token) <= 6:
            for target in _SUICIDE_TARGETS:
                if _levenshtein(token, target[:len(token)]) <= 2 or _levenshtein(token, target) <= 2:
                    return True
        if len(token) >= 7:
            for target in _SUICIDE_TARGETS:
                if _levenshtein(token, target) <= 3:
                    return True
    return False


def _fuzzy_crisis_match(text: str) -> bool:
    """
    Catch fuzzy misspellings and typos of common non-suicide crisis phrases:
    - kill myself / kill me (e.g. 'kil myself', 'kill myslf', 'kll myself', 'kil me')
    - want to die / gonna die (e.g. 'wana die', 'wnna die', 'want to dye')
    - end my life / take my life (e.g. 'end my lfe', 'nd my life', 'tak my life')
    - overdose (e.g. 'ovrdose', 'overdos', 'over dose', 'ovredose')
    """
    tokens = text.split()
    n = len(tokens)

    for token in tokens:
        if len(token) >= 5 and _levenshtein(token, "overdose") <= 2:
            return True
        if len(token) >= 6 and _levenshtein(token, "overdosing") <= 2:
            return True
    if "over dose" in text or "ovr dose" in text or "over dos" in text:
        return True

    for i, token in enumerate(tokens):
        # kill + myself/me within 5 tokens
        is_kill = (
            token in {"kill", "kil", "kll", "kils", "kiled", "kiling", "klling"}
            or (len(token) >= 4 and _levenshtein(token, "kill") <= 1)
        )
        if is_kill and token not in {"will", "till", "hill", "mill", "pill", "fill", "bill", "sill", "dill", "gill"}:
            for j in range(max(0, i - 4), min(n, i + 5)):
                t2 = tokens[j]
                if t2 in {"myself", "myslf", "mysef", "meself", "msyelf", "mysel", "me", "mysf"} or (
                    len(t2) >= 5 and _levenshtein(t2, "myself") <= 2
                ):
                    return True

        # want/wanna/gonna/trying + die/dye within 4 tokens
        is_want = token in {
            "want",
            "wants",
            "wanna",
            "wana",
            "wnna",
            "gonna",
            "gona",
            "going",
            "trying",
            "tryin",
            "plan",
            "planning",
            "plann",
        } or (len(token) >= 4 and _levenshtein(token, "wanna") <= 1)
        if is_want and token not in {"when", "what", "went", "worn", "warn"}:
            for j in range(max(0, i - 4), min(n, i + 5)):
                t2 = tokens[j]
                if t2 in {"die", "dye", "di", "dei", "dying", "diing"} or (
                    len(t2) == 3 and _levenshtein(t2, "die") <= 1 and t2 not in {"did", "dig", "dim", "dip", "dis", "due", "pie", "lie", "tie", "vie"}
                ):
                    return True

        # end/take + my + life within 5 tokens
        is_end = token in {"end", "ending", "nd", "endin", "take", "taking", "tak", "takin"}
        if is_end:
            for j in range(max(0, i - 4), min(n, i + 5)):
                t2 = tokens[j]
                if t2 in {"life", "lfe", "lif", "lyfe"} or (
                    len(t2) >= 3 and _levenshtein(t2, "life") <= 1 and t2 not in {"like", "live", "line", "lime", "lisa", "list", "lift"}
                ):
                    return True

    return False


def _fuzzy_at_risk_match(text: str) -> bool:
    """
    Catch fuzzy misspellings and typos of at-risk phrases:
    - self-harm (e.g. 'selfharm', 'slf harm', 'self hrm', 'slefharm')
    - cutting myself / hurt myself (e.g. 'cuting myself', 'hrt myself', 'hurting myslf')
    - hopeless / disappear / burden / worthless
    """
    tokens = text.split()
    n = len(tokens)

    for i, token in enumerate(tokens):
        # self + harm
        if token in {"selfharm", "slfharm", "selfhrm", "slefharm"} or (
            len(token) >= 7 and _levenshtein(token, "selfharm") <= 2
        ):
            return True
        if token in {"self", "slf", "slef"} or (len(token) == 4 and _levenshtein(token, "self") <= 1 and token not in {"sell", "seen", "seek", "send"}):
            for j in range(max(0, i - 3), min(n, i + 4)):
                t2 = tokens[j]
                if t2 in {"harm", "hrm", "har", "harming", "hrming"} or (
                    len(t2) >= 4 and _levenshtein(t2, "harm") <= 1 and t2 not in {"hard", "harp", "darm", "farm", "warm"}
                ):
                    return True

        # cutting/hurt + myself
        if token in {"cutting", "cuting", "ctting", "hurt", "hrt", "hurting", "hrting", "harming", "hrming"}:
            for j in range(max(0, i - 4), min(n, i + 5)):
                t2 = tokens[j]
                if t2 in {"myself", "myslf", "mysef", "meself", "msyelf", "mysel", "me"} or (
                    len(t2) >= 5 and _levenshtein(t2, "myself") <= 2
                ):
                    return True

        # single at-risk tokens with fuzzy matching
        if len(token) >= 7 and _levenshtein(token, "hopeless") <= 2:
            return True
        if len(token) >= 8 and _levenshtein(token, "disappear") <= 2:
            return True
        if len(token) >= 8 and _levenshtein(token, "worthless") <= 2:
            return True

    return False


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

    Detection order (first match wins):
      1. Exact regex crisis patterns (fast, zero false-positives)
      2. Fuzzy suicide keyword match (catches typos like "sucide", "suicde")
      3. Fuzzy crisis phrase match (catches typos like "kil myself", "ovrdose")
      4. Exact regex at-risk patterns
      5. Fuzzy at-risk phrase match (catches typos like "selfharm", "cuting myself")
      6. safe
    """
    if not user_message or not user_message.strip():
        return "unknown"

    text = _normalize(user_message)

    if any(pattern.search(text) for pattern in _CRISIS_RE):
        return "crisis"
    if _fuzzy_suicide_match(text):
        return "crisis"
    if _fuzzy_crisis_match(text):
        return "crisis"
    if any(pattern.search(text) for pattern in _AT_RISK_RE):
        return "at_risk"
    if _fuzzy_at_risk_match(text):
        return "at_risk"
    return "safe"

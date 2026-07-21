"""
ai_core/prompts/safety.py

Note: safety classification in this pipeline is intentionally RULE-BASED
(see agents/safety/rules.py), not LLM-based -- this is a deliberate design
choice from Part 1 so the mandatory safety gate is deterministic and
auditable rather than dependent on probabilistic model output.

This file exists as a placeholder for an optional secondary LLM-based
safety review layer, if the team later decides to add one on top of the
rule-based gate (e.g. for ambiguous cases the rules don't confidently
resolve). It is NOT currently wired into the graph.
"""

SAFETY_SECONDARY_REVIEW_PROMPT = """You are reviewing a message flagged as ambiguous by
a rule-based safety filter in a wellness companion app. Classify the message's safety
status as one of: "safe", "at_risk", "crisis". Be conservative -- if genuinely uncertain,
prefer the more cautious classification.

Message: {user_message}
"""

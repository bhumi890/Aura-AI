"""
ai_core/prompts/memory.py

Prompt for the long-term memory summarization agent (Part 6).
"""

MEMORY_SUMMARY_PROMPT = """You maintain a compact, evolving long-term memory profile of a
user for a wellness companion app. You will be given the EXISTING memory summary
and the NEW conversation turns since it was last updated.

Update the summary to incorporate new, durable information. Rules:
- Keep it under 200 words.
- Only include stable, recurring patterns (triggers, coping strategies that work
  for them, ongoing life circumstances, goals) -- NOT one-off details from a single
  conversation.
- Do not include anything the user would consider a privacy violation if
  repeated back verbatim in a casual tone -- phrase sensitively.
- Never fabricate details not present in the conversation.
- Do not include any crisis or self-harm details -- those are handled by a
  separate safety system and must not be persisted here.

EXISTING SUMMARY:
{existing_summary}

NEW TURNS:
{new_turns}
"""

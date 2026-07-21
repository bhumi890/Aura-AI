"""
ai_core/prompts/emotion.py

Prompt for the emotion-detection node.
"""

EMOTION_DETECTION_PROMPT = """You are an emotion-detection component inside a wellness
companion app. Read the user's message and recent conversation context, and identify
the primary emotion being expressed.

Return only a single primary emotion label (e.g. "anxious", "sad", "content", "frustrated",
"hopeful", "neutral") and a confidence score between 0 and 1. If the message is ambiguous
or emotionally flat, prefer "neutral" with a lower confidence rather than guessing.

Recent context:
{recent_history}

User message: {user_message}
"""

"""
Pydantic Schemas
Request and response schemas for all API endpoints.
These define the JSON contracts between frontend and backend.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ══════════════════════════════════════════════════════════════
#  Enums
# ══════════════════════════════════════════════════════════════

class MoodLevelEnum(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    NEUTRAL = "neutral"
    GOOD = "good"
    GREAT = "great"


class MessageRoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ══════════════════════════════════════════════════════════════
#  User Schemas
# ══════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    email: Optional[str] = None


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class AuthResponse(BaseModel):
    user_id: str
    username: str
    token: str  # session token (username:user_id base64, demo-level)


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════
#  Chat Schemas
# ══════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    """Request body for sending a chat message."""
    user_id: str = Field(..., description="User ID")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID, or null for new")
    message: str = Field(..., min_length=1, description="User's message text")


class AgentOutput(BaseModel):
    """Structured output from the AI agent pipeline."""
    emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None
    emotion_intensity: Optional[str] = None
    memory_summary: Optional[str] = None
    retrieved_docs: Optional[List[str]] = None
    safety_flag: Optional[bool] = True
    safety_reason: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""
    conversation_id: str
    message_id: str
    response: str = Field(..., description="AI assistant's response text")
    agent_output: Optional[AgentOutput] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════
#  Message Schemas
# ══════════════════════════════════════════════════════════════

class MessageResponse(BaseModel):
    id: str
    role: MessageRoleEnum
    content: str
    emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None
    is_voice_message: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    model_config = {"from_attributes": True}


class ConversationListItem(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════
#  Journal Schemas
# ══════════════════════════════════════════════════════════════

class JournalCreate(BaseModel):
    user_id: str
    title: Optional[str] = None
    content: str = Field(..., min_length=1)
    mood: Optional[MoodLevelEnum] = None
    tags: Optional[List[str]] = None


class JournalUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    mood: Optional[MoodLevelEnum] = None
    tags: Optional[List[str]] = None


class JournalResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str] = None
    content: str
    mood: Optional[str] = None
    emotion: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════
#  Mood Schemas
# ══════════════════════════════════════════════════════════════

class MoodCreate(BaseModel):
    user_id: str
    mood: MoodLevelEnum
    emotion: Optional[str] = None
    note: Optional[str] = None
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    sleep_quality: Optional[int] = Field(None, ge=1, le=10)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    activities: Optional[List[str]] = None


class MoodResponse(BaseModel):
    id: str
    user_id: str
    mood: str
    emotion: Optional[str] = None
    note: Optional[str] = None
    energy_level: Optional[int] = None
    sleep_quality: Optional[int] = None
    stress_level: Optional[int] = None
    activities: Optional[List[str]] = None
    logged_at: datetime

    model_config = {"from_attributes": True}


class MoodStats(BaseModel):
    """Aggregated mood statistics."""
    total_logs: int
    average_energy: Optional[float] = None
    average_sleep: Optional[float] = None
    average_stress: Optional[float] = None
    most_common_mood: Optional[str] = None
    mood_distribution: dict = {}


# ══════════════════════════════════════════════════════════════
#  Voice Schemas
# ══════════════════════════════════════════════════════════════

class TranscriptionResponse(BaseModel):
    """Response from speech-to-text."""
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None


class SynthesisRequest(BaseModel):
    """Request for text-to-speech."""
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(default="en", description="Language code")


# ══════════════════════════════════════════════════════════════
#  Wellness Plan Schemas
# ══════════════════════════════════════════════════════════════

class WellnessGoal(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False


class WellnessPlanCreate(BaseModel):
    user_id: str
    title: str = "My Wellness Plan"
    goals: Optional[List[WellnessGoal]] = None


class WellnessPlanUpdate(BaseModel):
    title: Optional[str] = None
    goals: Optional[List[WellnessGoal]] = None
    recommendations: Optional[List[str]] = None
    daily_routine: Optional[List[str]] = None
    coping_strategies: Optional[List[str]] = None


class WellnessPlanResponse(BaseModel):
    id: str
    user_id: str
    title: str
    goals: Optional[List[dict]] = None
    recommendations: Optional[List[str]] = None
    daily_routine: Optional[List[str]] = None
    coping_strategies: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════
#  History Schemas
# ══════════════════════════════════════════════════════════════

class HistoryQuery(BaseModel):
    user_id: str
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PaginatedResponse(BaseModel):
    items: List = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0

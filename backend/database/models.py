"""
Database Models
SQLAlchemy ORM models for the AI Emotional Wellness Companion.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from backend.database.connection import Base
import enum


# ── Enums ─────────────────────────────────────────────────────

class EmotionType(str, enum.Enum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    ANXIETY = "anxiety"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"
    LOVE = "love"
    HOPE = "hope"


class MoodLevel(str, enum.Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    NEUTRAL = "neutral"
    GOOD = "good"
    GREAT = "great"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ── Helper ────────────────────────────────────────────────────

def generate_uuid() -> str:
    return str(uuid.uuid4())


# ── User Model ────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)  # demo-level: stores plaintext for now
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")
    mood_logs = relationship("MoodLog", back_populates="user", cascade="all, delete-orphan")
    wellness_plans = relationship("WellnessPlan", back_populates="user", cascade="all, delete-orphan")


# ── Conversation Model ───────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan",
                            order_by="Message.created_at")


# ── Message Model ─────────────────────────────────────────────

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Agent metadata — stores outputs from AI agents
    emotion = Column(String(50), nullable=True)
    emotion_confidence = Column(Float, nullable=True)
    emotion_intensity = Column(String(20), nullable=True)
    safety_flag = Column(Boolean, default=True)
    agent_metadata = Column(JSON, nullable=True)  # Stores full agent pipeline output

    # Voice metadata
    is_voice_message = Column(Boolean, default=False)
    audio_duration = Column(Float, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


# ── Journal Entry Model ──────────────────────────────────────

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    mood = Column(SQLEnum(MoodLevel), nullable=True)
    emotion = Column(String(50), nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="journal_entries")


# ── Mood Log Model ────────────────────────────────────────────

class MoodLog(Base):
    __tablename__ = "mood_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    mood = Column(SQLEnum(MoodLevel), nullable=False)
    emotion = Column(String(50), nullable=True)
    note = Column(Text, nullable=True)
    energy_level = Column(Integer, nullable=True)  # 1-10
    sleep_quality = Column(Integer, nullable=True)  # 1-10
    stress_level = Column(Integer, nullable=True)  # 1-10
    activities = Column(JSON, nullable=True)  # List of activities
    logged_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="mood_logs")


# ── Wellness Plan Model ──────────────────────────────────────

class WellnessPlan(Base):
    __tablename__ = "wellness_plans"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), default="My Wellness Plan")
    goals = Column(JSON, nullable=True)  # List of goal objects
    recommendations = Column(JSON, nullable=True)  # AI-generated recommendations
    daily_routine = Column(JSON, nullable=True)  # Suggested daily routine
    coping_strategies = Column(JSON, nullable=True)  # Personalized coping strategies
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="wellness_plans")


# ── User Profile Model (long-term AI memory) ─────────────────

class UserProfile(Base):
    """
    Persists the AI's rolling memory summary per user across sessions.
    The memory_agent writes here after summarizing; the pipeline loads this
    at the start of each conversation so the AI remembers across logins.
    """
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    memory_summary = Column(Text, nullable=True)   # LLM-generated rolling summary
    last_summarized_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")

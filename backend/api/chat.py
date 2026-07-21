"""
Chat API Routes
Handles chat messaging between user and AI companion.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from backend.database.connection import get_db
from backend.database.schema import ChatRequest, ChatResponse, AgentOutput
from backend.database.crud import (
    get_or_create_user,
    create_conversation,
    get_conversation,
    create_message,
    get_conversation_messages,
)
from backend.database.models import MessageRole
from backend.utils.logger import api_logger

# AI Core
from ai_core.runtime.streaming import run_turn


router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.get("/health")
async def chat_health():
    """Health check for chat router."""
    return {"status": "ok", "service": "chat"}


@router.post("/", response_model=ChatResponse)
async def send_message(
    request_body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message and get an AI response.

    This endpoint:
    1. Saves the user's message to the database
    2. Forwards it to the AI supervisor agent (stub for now)
    3. Saves and returns the AI response

    The AI agent pipeline (Member 2's LangGraph) will be
    integrated here. For now, returns a placeholder response.
    """
    api_logger.info(f"Chat message from user {request_body.user_id}")

    # Ensure user exists
    await get_or_create_user(db, request_body.user_id)

    # Get or create conversation
    if request_body.conversation_id:
        conversation = await get_conversation(db, request_body.conversation_id)
        if not conversation:
            api_logger.warning(f"Conversation {request_body.conversation_id} not found, creating new one...")
            conversation = await create_conversation(db, request_body.user_id, title=request_body.message[:40] + ("..." if len(request_body.message) > 40 else ""))
    else:
        conversation = await create_conversation(db, request_body.user_id, title=request_body.message[:40] + ("..." if len(request_body.message) > 40 else ""))
        api_logger.info(f"Created new conversation: {conversation.id} ({conversation.title})")

    if conversation and conversation.title == "New Conversation":
        conversation.title = request_body.message[:40] + ("..." if len(request_body.message) > 40 else "")

    # Save user message
    user_message = await create_message(
        db,
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=request_body.message,
    )


    # ─── AI Agent Pipeline ────────────────────────────────────
    ai_app = getattr(request.app.state, 'ai_app', None)

    if ai_app is not None:
        # Run through the full LangGraph multi-agent pipeline
        try:
            session_id = request_body.conversation_id or conversation.id
            ai_response_text = ""

            async for chunk in run_turn(
                ai_app,
                user_id=request_body.user_id,
                session_id=session_id,
                user_message=request_body.message,
            ):
                ai_response_text += chunk

            if not ai_response_text:
                ai_response_text = (
                    "I'm here for you. Could you tell me a bit more "
                    "about what's on your mind?"
                )

            # Extract agent metadata from the pipeline state
            try:
                final_state = await ai_app.aget_state({"configurable": {"thread_id": session_id}})
                state_dict = final_state.values if final_state else {}
            except Exception as e:
                api_logger.warning(f"Could not retrieve final graph state: {e}")
                state_dict = {}

            agent_output = AgentOutput(
                emotion=state_dict.get("emotion") or "neutral",
                emotion_confidence=state_dict.get("emotion_confidence") or 0.8,
                emotion_intensity="medium",
                memory_summary=state_dict.get("memory_summary"),
                retrieved_docs=[d.get("content", "")[:200] for d in state_dict.get("retrieved_documents", [])] if state_dict.get("retrieved_documents") else None,
                safety_flag=(state_dict.get("safety_status") == "safe"),
                safety_reason=f"safety_status: {state_dict.get('safety_status', 'safe')}",
            )

            if state_dict.get("memory_summary"):
                from backend.database.crud import upsert_user_profile
                await upsert_user_profile(db, request_body.user_id, state_dict.get("memory_summary"))

            api_logger.info(f"AI pipeline response: {len(ai_response_text)} chars")


        except Exception as e:
            api_logger.error(f"AI pipeline error: {e}")
            ai_response_text = (
                "I hear you. Thank you for sharing that with me. "
                "I'm here to support you through whatever you're feeling. "
                "Would you like to tell me more about what's on your mind?"
            )
            agent_output = AgentOutput(
                emotion="neutral",
                emotion_confidence=0.5,
                safety_flag=True,
                safety_reason="fallback — AI pipeline error",
            )
    else:
        # AI pipeline not available — use fallback
        api_logger.warning("AI pipeline not available, using fallback response")
        ai_response_text = (
            "I hear you. Thank you for sharing that with me. "
            "I'm here to support you through whatever you're feeling. "
            "Would you like to tell me more about what's on your mind?"
        )
        agent_output = AgentOutput(
            emotion="neutral",
            emotion_confidence=0.5,
            emotion_intensity="low",
            safety_flag=True,
            safety_reason="fallback — AI pipeline not loaded",
        )
    # ─── End AI Pipeline ──────────────────────────────────────

    # Save AI response
    ai_message = await create_message(
        db,
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=ai_response_text,
        emotion=agent_output.emotion,
        emotion_confidence=agent_output.emotion_confidence,
        emotion_intensity=agent_output.emotion_intensity,
        safety_flag=agent_output.safety_flag,
        agent_metadata=agent_output.model_dump(),
    )

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=ai_message.id,
        response=ai_response_text,
        agent_output=agent_output,
        created_at=ai_message.created_at,
    )


@router.get("/conversations/{user_id}")
async def get_user_conversations(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all conversations for a user."""
    from backend.database.crud import get_user_conversations as fetch_convos

    conversations, total = await fetch_convos(db, user_id)
    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in conversations
        ],
        "total": total,
    }


@router.get("/conversation/{conversation_id}")
async def get_conversation_detail(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all its messages."""
    conversation = await get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role.value,
                "content": m.content,
                "emotion": m.emotion,
                "created_at": m.created_at.isoformat(),
            }
            for m in conversation.messages
        ],
    }


@router.websocket("/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time chat.
    Frontend can connect for streaming responses.
    """
    await websocket.accept()
    api_logger.info(f"WebSocket connected: user {user_id}")

    ai_app = getattr(websocket.app.state, 'ai_app', None)
    session_id = str(uuid.uuid4())

    try:
        while True:
            data = await websocket.receive_text()

            if ai_app is not None:
                try:
                    full_response = ""
                    async for chunk in run_turn(
                        ai_app,
                        user_id=user_id,
                        session_id=session_id,
                        user_message=data,
                    ):
                        full_response += chunk
                        await websocket.send_json({
                            "type": "stream",
                            "content": chunk,
                            "timestamp": datetime.utcnow().isoformat(),
                        })

                    await websocket.send_json({
                        "type": "message",
                        "content": full_response,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                except Exception as e:
                    api_logger.error(f"WebSocket AI pipeline error: {e}")
                    await websocket.send_json({
                        "type": "message",
                        "content": "I'm here to help. Could you tell me more?",
                        "emotion": "neutral",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            else:
                response = {
                    "type": "message",
                    "content": "I received your message. I'm here to help.",
                    "emotion": "neutral",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await websocket.send_json(response)

    except WebSocketDisconnect:
        api_logger.info(f"WebSocket disconnected: user {user_id}")

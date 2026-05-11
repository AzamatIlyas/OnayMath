from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.db.models.education import AppUser, ChatMessage, Topic
from app.schema.api import AssistantChatRequest
from app.service.ai import generate_groq_response
from app.service.platform import build_assistant_reply, serialize_chat_message, split_text_chunks

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/history")
async def get_history(
    limit: int = Query(default=50, ge=1, le=200),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        (
            await db.execute(
                select(ChatMessage)
                .where(ChatMessage.user_id == user.id)
                .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )

    return {"data": [serialize_chat_message(row) for row in rows]}


@router.post("/chat")
async def chat_stream(
    payload: AssistantChatRequest,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    topic = None
    if payload.topicId:
        topic = (await db.execute(select(Topic).where(Topic.id == payload.topicId))).scalar_one_or_none()

    topic_title = topic.title if topic else None
    response_text = await generate_groq_response(
        message=payload.message,
        topic_title=topic_title,
        history=payload.conversationHistory,
    )
    if not response_text:
        response_text = build_assistant_reply(payload.message, topic=topic, history=payload.conversationHistory)
    topic_context = topic.id if topic else None

    user_message = ChatMessage(
        user_id=user.id,
        role="USER",
        content=payload.message.strip(),
        topic_context=topic_context,
    )
    assistant_message = ChatMessage(
        user_id=user.id,
        role="ASSISTANT",
        content=response_text,
        topic_context=topic_context,
    )
    db.add_all([user_message, assistant_message])
    await db.commit()

    async def events():
        for chunk in split_text_chunks(response_text, chunk_size=34):
            data = json.dumps({"type": "chunk", "chunk": chunk}, ensure_ascii=False)
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.01)

    return StreamingResponse(events(), media_type="text/event-stream")

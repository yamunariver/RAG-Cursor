import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_roles
from app.db.models import Conversation, KnowledgeBase, Message, User
from app.db.session import get_db
from app.schemas import ChatRequest, ChatResponse, Citation
from app.services.ollama import chat_completion
from app.services.retrieval.context import build_messages
from app.services.retrieval.search import build_context, rerank_candidates, retrieve_candidates

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.knowledge_base_id is None:
        raise HTTPException(status_code=400, detail="knowledge_base_id is required")

    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == payload.knowledge_base_id))
    kb = kb_result.scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    conversation_id = payload.conversation_id
    if conversation_id is None:
        conversation = Conversation(user_id=user.id, knowledge_base_id=kb.id, title=payload.question[:80])
        db.add(conversation)
        await db.flush()
        conversation_id = conversation.id
    else:
        conv_result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        conversation = conv_result.scalar_one_or_none()
        if conversation is None or conversation.user_id != user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")

    candidates = await retrieve_candidates(kb.qdrant_collection, payload.question)
    reranked = await rerank_candidates(payload.question, candidates)
    context, citation_payload = build_context(reranked)

    history_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
    )
    history = [{"role": m.role, "content": m.content} for m in history_result.scalars().all()[-6:]]

    messages = build_messages(payload.question, context, history)
    answer_parts: list[str] = []
    async for chunk in chat_completion(messages, stream=False):
        answer_parts.append(chunk["message"]["content"])

    answer = answer_parts[0] if answer_parts else ""
    citations = [Citation(**item) for item in citation_payload]

    db.add(Message(conversation_id=conversation_id, role="user", content=payload.question))
    db.add(
        Message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            citations_json=[c.model_dump(mode="json") for c in citations],
        )
    )
    await db.commit()

    return ChatResponse(answer=answer, citations=citations, conversation_id=conversation_id)


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.knowledge_base_id is None:
        raise HTTPException(status_code=400, detail="knowledge_base_id is required")

    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == payload.knowledge_base_id))
    kb = kb_result.scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    candidates = await retrieve_candidates(kb.qdrant_collection, payload.question)
    reranked = await rerank_candidates(payload.question, candidates)
    context, citation_payload = build_context(reranked)
    messages = build_messages(payload.question, context)

    async def event_generator():
        yield json.dumps({"type": "citations", "data": citation_payload}) + "\n"
        async for line in chat_completion(messages, stream=True):
            yield line + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@router.get("/conversations")
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()

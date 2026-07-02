import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_roles
from app.db.models import AuditLog, KnowledgeBase, User
from app.db.session import get_db
from app.schemas import KnowledgeBaseCreate, KnowledgeBaseResponse, SearchRequest, SearchResult
from app.services.qdrant_client import ensure_collection
from app.services.retrieval.search import retrieve_candidates

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(KnowledgeBase).where(KnowledgeBase.is_active.is_(True))
    if user.role not in {"admin"} and user.department:
        query = query.where(
            (KnowledgeBase.department == user.department) | (KnowledgeBase.department.is_(None))
        )
    result = await db.execute(query.order_by(KnowledgeBase.name.asc()))
    return result.scalars().all()


@router.post("", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    collection = f"kb_{payload.slug.replace('-', '_')}"
    ensure_collection(collection)

    kb = KnowledgeBase(
        name=payload.name,
        slug=payload.slug,
        department=payload.department,
        description=payload.description,
        qdrant_collection=collection,
    )
    db.add(kb)
    await db.flush()
    db.add(
        AuditLog(
            user_id=user.id,
            action="knowledge_base_create",
            resource_type="knowledge_base",
            resource_id=str(kb.id),
            details_json={"slug": payload.slug},
        )
    )
    await db.commit()
    await db.refresh(kb)
    return kb


@router.post("/search", response_model=list[SearchResult])
async def search(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == payload.knowledge_base_id))
    kb = kb_result.scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    hits = await retrieve_candidates(
        kb.qdrant_collection,
        payload.query,
        top_k=payload.top_k,
        filters=payload.filters,
    )
    return [
        SearchResult(
            document_id=uuid.UUID(hit["document_id"]),
            filename=hit.get("filename", ""),
            chunk_index=hit.get("chunk_index", 0),
            content=hit["content"],
            score=float(hit.get("score", 0.0)),
            page_number=hit.get("page_number"),
        )
        for hit in hits
    ]

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_roles
from app.db.models import AuditLog, Document, KnowledgeBase, User
from app.db.session import get_db
from app.schemas import DocumentResponse
from app.services.storage import scan_bytes, upload_bytes
from app.workers.tasks import ingest_document_task

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    knowledge_base_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("editor", "admin")),
):
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id))
    kb = kb_result.scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    data = await file.read()
    scan_bytes(data)
    object_name = f"{kb.slug}/{uuid.uuid4()}/{file.filename}"
    storage_path = upload_bytes(object_name, data, file.content_type or "application/octet-stream")

    document = Document(
        knowledge_base_id=kb.id,
        filename=file.filename or "upload.bin",
        file_type="pending",
        storage_path=storage_path,
        content_hash="pending",
        status="queued",
        metadata_json={"uploaded_by": str(user.id)},
    )
    db.add(document)
    await db.flush()
    db.add(
        AuditLog(
            user_id=user.id,
            action="document_upload",
            resource_type="document",
            resource_id=str(document.id),
            details_json={"filename": document.filename},
        )
    )
    await db.commit()
    await db.refresh(document)

    ingest_document_task.delay(str(document.id))
    return document


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    knowledge_base_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document)
        .where(Document.knowledge_base_id == knowledge_base_id)
        .order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{document_id}/reindex")
async def reindex_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("editor", "admin")),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    document.status = "queued"
    await db.commit()
    ingest_document_task.delay(str(document.id))
    return {"status": "queued", "document_id": str(document_id)}

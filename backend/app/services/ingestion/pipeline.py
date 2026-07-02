import asyncio
import uuid

from qdrant_client.http.models import PointStruct
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Document, DocumentChunk, KnowledgeBase
from app.services.ingestion.chunking import semantic_chunk
from app.services.ingestion.detection import detect_file_type, sha256_bytes
from app.services.ingestion.extraction import extract_text
from app.services.ingestion.ocr import ocr_image, ocr_pdf
from app.services.ollama import embed_texts
from app.services.qdrant_client import ensure_collection, upsert_vectors
from app.services.storage import download_bytes, scan_bytes


async def ingest_document(db: AsyncSession, document_id: uuid.UUID) -> None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one()
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == document.knowledge_base_id))
    knowledge_base = kb_result.scalar_one()

    document.status = "processing"
    await db.commit()

    try:
        data = download_bytes(document.storage_path)
        scan_bytes(data)

        file_type, mime_type = detect_file_type(document.filename, data)
        content_hash = sha256_bytes(data)

        duplicate = await db.execute(
            select(Document).where(
                Document.knowledge_base_id == document.knowledge_base_id,
                Document.content_hash == content_hash,
                Document.id != document.id,
            )
        )
        if duplicate.scalar_one_or_none():
            document.status = "duplicate"
            document.error_message = "Duplicate content hash detected"
            await db.commit()
            return

        ocr_text = None
        page_count = None
        if settings.enable_ocr and file_type == "pdf" and len(data) > 0:
            extracted, page_count = extract_text("pdf", data)
            if len(extracted.strip()) < 50:
                ocr_text, page_count = ocr_pdf(data)
        elif settings.enable_ocr and file_type in {"png", "jpg", "jpeg", "tiff", "tif"}:
            ocr_text = ocr_image(data)

        text, extracted_pages = extract_text(file_type, data, ocr_text=ocr_text)
        page_count = page_count or extracted_pages

        chunks = semantic_chunk(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            document.status = "failed"
            document.error_message = "No extractable text"
            await db.commit()
            return

        vectors = await embed_texts(chunks)
        ensure_collection(knowledge_base.qdrant_collection, vector_size=len(vectors[0]))

        points: list[PointStruct] = []
        for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
            chunk_id = uuid.uuid4()
            point_id = str(chunk_id)
            db.add(
                DocumentChunk(
                    id=chunk_id,
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk,
                    token_count=len(chunk.split()),
                    page_number=None,
                    qdrant_point_id=point_id,
                    metadata_json={"filename": document.filename, "file_type": file_type},
                )
            )
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "document_id": str(document.id),
                        "knowledge_base_id": str(knowledge_base.id),
                        "chunk_index": index,
                        "content": chunk,
                        "filename": document.filename,
                        "file_type": file_type,
                        "department": knowledge_base.department,
                    },
                )
            )

        upsert_vectors(knowledge_base.qdrant_collection, points)

        document.file_type = file_type
        document.mime_type = mime_type
        document.content_hash = content_hash
        document.page_count = page_count
        document.status = "indexed"
        document.metadata_json = {
            **document.metadata_json,
            "chunk_count": len(chunks),
        }
        await db.commit()
    except Exception as exc:
        document.status = "failed"
        document.error_message = str(exc)
        await db.commit()
        raise


def ingest_document_sync(document_id: str) -> None:
    from app.db.session import SessionLocal

    async def _run() -> None:
        async with SessionLocal() as db:
            await ingest_document(db, uuid.UUID(document_id))

    asyncio.run(_run())

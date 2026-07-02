from app.services.ingestion.pipeline import ingest_document_sync
from app.workers.celery_app import celery_app


@celery_app.task(name="ingest_document")
def ingest_document_task(document_id: str) -> None:
    ingest_document_sync(document_id)

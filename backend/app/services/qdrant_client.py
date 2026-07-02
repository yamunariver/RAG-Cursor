from functools import lru_cache

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    HnswConfigDiff,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from app.config import settings


@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def ensure_collection(collection_name: str, vector_size: int = 1024) -> None:
    client = get_qdrant_client()
    collections = {c.name for c in client.get_collections().collections}
    if collection_name in collections:
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        hnsw_config=HnswConfigDiff(m=16, ef_construct=128),
    )
    for field in ("document_id", "knowledge_base_id", "department", "file_type"):
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )


def upsert_vectors(collection_name: str, points: list[PointStruct]) -> None:
    client = get_qdrant_client()
    client.upsert(collection_name=collection_name, points=points)


def hybrid_search(
    collection_name: str,
    query_vector: list[float],
    top_k: int,
    filters: dict | None = None,
) -> list[dict]:
    client = get_qdrant_client()
    qdrant_filter = None
    if filters:
        conditions = [
            FieldCondition(key=key, match=MatchValue(value=value))
            for key, value in filters.items()
        ]
        qdrant_filter = Filter(must=conditions)

    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        query_filter=qdrant_filter,
        with_payload=True,
    )
    return [
        {
            "id": str(hit.id),
            "score": hit.score,
            **hit.payload,
        }
        for hit in results
    ]

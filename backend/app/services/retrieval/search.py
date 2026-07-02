from rank_bm25 import BM25Okapi

from app.config import settings
from app.services.ollama import embed_query, rerank
from app.services.qdrant_client import hybrid_search


async def retrieve_candidates(
    collection_name: str,
    query: str,
    top_k: int | None = None,
    filters: dict | None = None,
) -> list[dict]:
    top_k = top_k or settings.retrieval_top_k
    query_vector = await embed_query(query)
    vector_hits = hybrid_search(collection_name, query_vector, top_k=top_k, filters=filters)

    if not vector_hits:
        return []

    tokenized_corpus = [hit["content"].split() for hit in vector_hits]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(query.split())

    merged: list[dict] = []
    for hit, bm25_score in zip(vector_hits, bm25_scores, strict=True):
        vector_score = hit.get("score", 0.0)
        combined = settings.hybrid_vector_weight * vector_score + (1 - settings.hybrid_vector_weight) * float(
            bm25_score
        )
        merged.append({**hit, "score": combined})

    merged.sort(key=lambda item: item["score"], reverse=True)
    return merged[:top_k]


async def rerank_candidates(query: str, candidates: list[dict]) -> list[dict]:
    if not candidates:
        return []

    passages = [item["content"] for item in candidates]
    ranked = await rerank(query, passages)
    reranked: list[dict] = []
    for idx, score in ranked[: settings.rerank_top_k]:
        item = dict(candidates[idx])
        item["score"] = score
        reranked.append(item)
    return reranked


def build_context(candidates: list[dict]) -> tuple[str, list[dict]]:
    blocks: list[str] = []
    citations: list[dict] = []
    for idx, item in enumerate(candidates, start=1):
        blocks.append(f"[{idx}] {item['content']}")
        citations.append(
            {
                "document_id": item.get("document_id"),
                "filename": item.get("filename"),
                "chunk_index": item.get("chunk_index"),
                "page_number": item.get("page_number"),
                "snippet": item["content"][:500],
                "score": item.get("score", 0.0),
            }
        )
    return "\n\n".join(blocks), citations

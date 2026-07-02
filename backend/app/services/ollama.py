import httpx

from app.config import settings


async def embed_texts(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0) as client:
        vectors: list[list[float]] = []
        for text in texts:
            response = await client.post(
                "/api/embeddings",
                json={"model": settings.embedding_model, "prompt": text},
            )
            response.raise_for_status()
            vectors.append(response.json()["embedding"])
        return vectors


async def embed_query(text: str) -> list[float]:
    vectors = await embed_texts([text])
    return vectors[0]


async def chat_completion(messages: list[dict], stream: bool = False):
    payload = {
        "model": settings.chat_model,
        "messages": messages,
        "stream": stream,
    }
    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=None) as client:
        if stream:
            async with client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield line
        else:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            yield response.json()


async def rerank(query: str, passages: list[str]) -> list[tuple[int, float]]:
    """Score passages with cross-encoder reranker via Ollama generate API."""
    scores: list[tuple[int, float]] = []
    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0) as client:
        for idx, passage in enumerate(passages):
            prompt = f"Query: {query}\nPassage: {passage}\nRelevance score 0-1:"
            response = await client.post(
                "/api/generate",
                json={"model": settings.reranker_model, "prompt": prompt, "stream": False},
            )
            if response.status_code != 200:
                scores.append((idx, 0.0))
                continue
            text = response.json().get("response", "0").strip()
            try:
                score = float(text.split()[0])
            except (ValueError, IndexError):
                score = 0.0
            scores.append((idx, score))
    scores.sort(key=lambda item: item[1], reverse=True)
    return scores

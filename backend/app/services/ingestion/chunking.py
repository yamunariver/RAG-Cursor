def semantic_chunk(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    if not text.strip():
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= chunk_size:
            current = f"{current}\n\n{paragraph}".strip()
            continue

        if current:
            chunks.append(current)
        if len(paragraph) <= chunk_size:
            current = paragraph
            continue

        start = 0
        while start < len(paragraph):
            end = start + chunk_size
            chunks.append(paragraph[start:end])
            start = max(end - overlap, start + 1)
        current = ""

    if current:
        chunks.append(current)

    if not chunks and text:
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = max(end - overlap, start + 1)

    return chunks

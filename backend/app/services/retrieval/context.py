SYSTEM_PROMPT = """You are an enterprise knowledge assistant.
Answer using only the provided context.
Cite sources using bracket numbers like [1], [2].
If the answer is not in the context, say you do not know."""


def build_messages(question: str, context: str, history: list[dict] | None = None) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append(
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        }
    )
    return messages

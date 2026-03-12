# retriever.py
# Thin wrapper around storage.retrieve_relevant_chunks that formats
# the results into a numbered context block ready to drop into a prompt.

import storage


def get_context(query, filename, top_k=5):
    chunks = storage.retrieve_relevant_chunks(query, filename, top_k=top_k)
    if not chunks:
        return ""

    # Number each excerpt so the model can reference them if needed
    parts = [f"[Excerpt {i}]\n{chunk}" for i, chunk in enumerate(chunks, 1)]
    return "\n\n".join(parts)

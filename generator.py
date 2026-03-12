# generator.py
# Sends the retrieved document excerpts + user question to Claude
# and returns the answer. Keeps a short chat history for follow-up questions.

import os
import anthropic

# Reuse the same client across requests instead of re-initializing every call
_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. Export it before running the app."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


# Keep the system prompt strict so the model doesn't start hallucinating
# answers that aren't actually in the document
SYSTEM_PROMPT = (
    "You are a document assistant. The user will ask questions about a document they uploaded. "
    "You will be given relevant excerpts from that document. "
    "Answer using only the provided excerpts. "
    "If the answer is not in the excerpts, say so — do not guess or make things up."
)


def generate_answer(query, context, chat_history=None):
    client = _get_client()

    if not context:
        return "Could not find relevant content in the document for that question."

    # Excerpts go first so the model reads the source material before the question
    user_message = f"Document excerpts:\n{context}\n\nQuestion: {query}"

    messages = []
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        system=SYSTEM_PROMPT,
        messages=messages,
        temperature=0.2,  # low temperature keeps answers factual and consistent
        max_tokens=1024,
    )

    return response.content[0].text.strip()

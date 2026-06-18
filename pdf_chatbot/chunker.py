# chunker.py
# Splits document text into smaller overlapping chunks before embedding.
# We split on sentence boundaries instead of raw character count so we
# don't end up cutting a sentence in half and losing context.

import re
import document_parser


def split_sentences(text):
    # Split on period/exclamation/question mark followed by whitespace.
    # Not perfect for edge cases like "Dr. Smith" but good enough for most docs.
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text, chunk_size=400, overlap=80):
    sentences = split_sentences(text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= chunk_size:
            current += (" " if current else "") + sentence
        else:
            if current:
                chunks.append(current.strip())
            # Pull the tail of the previous chunk into the new one so
            # questions that span a chunk boundary still get answered correctly
            if chunks and overlap > 0:
                current = chunks[-1][-overlap:] + " " + sentence
            else:
                current = sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


def chunk_file(filepath, chunk_size=400, overlap=80):
    text = document_parser.extract_text(filepath)

    if text is None:
        raise ValueError(f"Could not extract text from {filepath}")
    if not text.strip():
        raise ValueError(f"{filepath} has no readable text")

    return chunk_text(text, chunk_size=chunk_size, overlap=overlap)

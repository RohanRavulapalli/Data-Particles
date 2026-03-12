# storage.py
# Embeds document chunks and stores them in a local DuckDB database.
# Retrieval is done with cosine similarity against the query embedding.
#
# Embedding strategy:
#   - If sentence-transformers is installed, use all-MiniLM-L6-v2 (better quality)
#   - Otherwise fall back to TF-IDF via scikit-learn (no extra install needed)
#
# DuckDB keeps everything in a single local file - there is no server or cloud

import os
import json
import numpy as np
import duckdb
import chunker

DB_PATH = os.path.join(os.path.dirname(__file__), "chatbot_store.duckdb")

# Module-level embedder so we only load the model once per process
_embedder = None
_use_tfidf = False


def _load_embedder():
    global _embedder, _use_tfidf
    if _embedder is not None:
        return
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        _use_tfidf = False
        print("Loaded sentence-transformers model")
    except ImportError:
        _use_tfidf = True
        print("sentence-transformers not found, falling back to TF-IDF")


def _embed_texts(texts):
    _load_embedder()
    if not _use_tfidf:
        vecs = _embedder.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return np.array(vecs, dtype=np.float32)
    else:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import normalize
        vec = TfidfVectorizer(max_features=1536)
        matrix = vec.fit_transform(texts).toarray().astype(np.float32)
        return normalize(matrix)


def _embed_query(query, all_chunks):
    _load_embedder()
    if not _use_tfidf:
        vec = _embedder.encode([query], show_progress_bar=False, normalize_embeddings=True)
        return np.array(vec[0], dtype=np.float32)
    else:
        # TF-IDF needs the full corpus to build its vocabulary, so we append
        # the query to the chunks and grab the last row.
        # We also pad/trim to match the stored embedding size exactly,
        # since max_features can vary slightly depending on corpus vocabulary.
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import normalize

        corpus = all_chunks + [query]
        vec = TfidfVectorizer(max_features=1536)
        matrix = vec.fit_transform(corpus).toarray().astype(np.float32)
        matrix = normalize(matrix)
        query_vec = matrix[-1]

        # Stored embeddings were built with a different corpus so their
        # dimension may differ by a few features. Pad or trim to match.
        stored_dim = len(json.loads(
            duckdb.connect(DB_PATH).execute(
                "SELECT embedding FROM documents LIMIT 1"
            ).fetchone()[0]
        ))

        if len(query_vec) < stored_dim:
            query_vec = np.pad(query_vec, (0, stored_dim - len(query_vec)))
        elif len(query_vec) > stored_dim:
            query_vec = query_vec[:stored_dim]

        return query_vec


def _get_conn():
    conn = duckdb.connect(DB_PATH)
    # Create table on first run; no-op after that
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            filename TEXT,
            chunk_index INTEGER,
            chunk_text TEXT,
            embedding TEXT
        )
    """)
    return conn


def store_document(filepath, filename):
    print(f"Processing {filename}...")
    chunks = chunker.chunk_file(filepath)
    print(f"{len(chunks)} chunks created")

    embeddings = _embed_texts(chunks)

    conn = _get_conn()

    # Delete any existing rows for this file so re-uploads don't duplicate data
    conn.execute("DELETE FROM documents WHERE filename = ?", [filename])

    result = conn.execute("SELECT COALESCE(MAX(id), 0) FROM documents").fetchone()
    next_id = result[0] + 1

    rows = [
        (next_id + i, filename, i, chunk, json.dumps(emb.tolist()))
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ]

    conn.executemany(
        "INSERT INTO documents (id, filename, chunk_index, chunk_text, embedding) VALUES (?, ?, ?, ?, ?)",
        rows
    )
    conn.close()
    print(f"Stored {len(chunks)} chunks for {filename}")
    return len(chunks)


def retrieve_relevant_chunks(query, filename, top_k=5):
    conn = _get_conn()
    rows = conn.execute(
        "SELECT chunk_text, embedding FROM documents WHERE filename = ?",
        [filename]
    ).fetchall()
    conn.close()

    if not rows:
        return []

    all_chunks = [r[0] for r in rows]
    all_embeddings = np.array([json.loads(r[1]) for r in rows], dtype=np.float32)
    query_vec = _embed_query(query, all_chunks)

    # Dot product works as cosine similarity since embeddings are normalized
    scores = all_embeddings @ query_vec
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [all_chunks[i] for i in top_indices]


def list_documents():
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT filename FROM documents").fetchall()
    conn.close()
    return [r[0] for r in rows]


def delete_document(filename):
    conn = _get_conn()
    conn.execute("DELETE FROM documents WHERE filename = ?", [filename])
    conn.close()
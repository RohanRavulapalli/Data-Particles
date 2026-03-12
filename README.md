# docchat

A local RAG chatbot for PDF and DOCX files. Upload a document, ask questions, get answers grounded in the document content.

## How it works

1. You upload a PDF or DOCX file through the web interface
2. The document is split into overlapping text chunks
3. Each chunk is embedded and stored in a local DuckDB database
4. When you ask a question, the most relevant chunks are retrieved using cosine similarity
5. Those chunks are sent to Claude along with your question to generate an answer

## Stack

- Flask — web server
- PyMuPDF — PDF text extraction
- python-docx — DOCX text extraction
- scikit-learn TF-IDF — local embeddings (no API key needed)
- DuckDB — local vector storage
- Anthropic Claude (claude-sonnet-4-6) — answer generation

## Setup

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Set your Anthropic API key

Mac/Linux:
```
export ANTHROPIC_API_KEY=your-key-here
```

Windows:
```
set ANTHROPIC_API_KEY=your-key-here
```

### 3. Run

```
python app.py
```

Then open http://localhost:5000 in your browser.

## Optional: better embeddings

If you want higher quality retrieval, install sentence-transformers:

```
pip install sentence-transformers
```

The app will use it automatically if it is installed. If not, it falls back to TF-IDF which works fine for most documents.

## File structure

```
docchat/
  app.py                  Flask routes and session handling
  document_parser.py      PDF and DOCX text extraction
  chunker.py              Sentence-aware text chunking with overlap
  storage.py              Embeddings and DuckDB read/write
  retriever.py            Similarity search and context formatting
  generator.py            Claude API call
  templates/
    index.html            Web UI
  uploads/                Uploaded files (auto-created, not committed)
  chatbot_store.duckdb    Local database (auto-created, not committed)
  requirements.txt
```

## Notes

- The DuckDB file and uploads folder are created automatically on first run
- Re-uploading a file with the same name replaces the old version in the database
- Chat history is stored per session and limited to the last 10 turns

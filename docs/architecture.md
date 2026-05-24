# Architecture

Digital Priestess is split into a local web frontend and a local RAG backend. The current slice uses SQLite for a durable local document/chunk index and keeps vector search as a later upgrade.

## Runtime Shape

- `frontend/`: Vite React TypeScript app served on localhost.
- `backend/`: FastAPI service bound to `127.0.0.1`.
- LM Studio: local model server reached through `LM_STUDIO_BASE_URL`.
- Archive: user-approved directory referenced by `ARCHIVE_ROOT`.
- Derived data: local ignored path configured by `DATA_DIR`, including `digital_priestess.sqlite3`.

## Data Flow

1. The browser sends a chat request with a message and persona mode.
2. The backend loads citation-ready chunks from the local SQLite index.
3. If the index is empty, the backend can fall back to scanning supported files under `ARCHIVE_ROOT`.
4. The retriever ranks chunks with a lightweight local keyword score.
5. The prompt builder combines persona rules, grounding rules, and retrieved passages.
6. The LM Studio adapter asks the local model for an answer.
7. If LM Studio is unavailable, the backend returns a cautious fallback answer and the same candidate citations.

## Local-Only Policy

The MVP assumes no cloud calls at runtime. Model inference uses LM Studio on localhost. OCR and document parsing use local libraries only. Any optional cloud integration must be explicit, disabled by default, and documented before it is added.

## Indexing

`POST /api/archive/index` scans extractable files, hashes them, and writes document metadata plus chunks to SQLite. Unchanged files are skipped using file hash and modified time. The scanner currently supports text, Markdown, and HTML by default. PDF, DOCX, RTF, and image OCR are optional local extractors enabled by installing the backend ingest extra; image OCR also requires `ENABLE_OCR=true` and a local Tesseract installation.

## Next Layers

- LanceDB or another embedded vector store for embeddings.
- Incremental indexing based on file hash and modified time.
- Source taxonomy for journal, dream log, book excerpt, correspondence table, ritual note, and web reference.
- Streaming responses in the frontend.
# Digital Priestess

Digital Priestess is a fully local archivist and occult reference app for a private mixed archive of journals, notes, and reference material. The MVP is a local web app with a Python RAG backend, a React chat interface, citation-first answers, and a configurable priestess/archivist persona.

## Privacy Boundary

- Runtime is local-only by default.
- The backend binds to `127.0.0.1`.
- The app talks to LM Studio through a local OpenAI-compatible endpoint, but the model can be any local model served by LM Studio.
- Source archive files are read in place and are not copied into the repository.
- Derived indexes, local databases, OCR cache, logs, and environment files are ignored by git.

## Current Slice

This first implementation includes:

- A FastAPI backend with local settings, health checks, persona modes, archive status, and a chat endpoint.
- A local SQLite archive index for document metadata and citation-ready chunks.
- A local retrieval path for indexed Markdown, plain text, and HTML files under an approved archive root.
- Optional local extractors for PDF, DOCX, RTF, and image OCR when the backend ingest extra and local OCR tooling are installed.
- An LM Studio adapter that calls `/v1/chat/completions` when the local model server is available.
- A fallback answer path that still returns candidate citations when LM Studio is offline.
- A Vite React chat UI with mode controls, model/archive/index status, message flow, and a citation panel.

Vector embeddings, source viewing, streaming responses, and richer OCR/page metadata are planned next layers.

## Setup

1. Copy `.env.example` to `.env` and set `ARCHIVE_ROOT` to the folder you want to index.
2. Start LM Studio and enable its local server, usually at `http://127.0.0.1:1234/v1`.
3. Install and run the backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --host 127.0.0.1 --port 8787 --reload
```

Install optional local extractors when you are ready to index PDFs, DOCX, RTF, or OCR-backed images:

```powershell
cd backend
python -m pip install -e ".[dev,ingest]"
```

4. Install and run the frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

5. Open the Vite URL shown in the terminal, usually `http://127.0.0.1:5173`.

## Configuration

The backend reads local configuration from environment variables or `.env`:

- `LM_STUDIO_BASE_URL`: Local LM Studio API base URL.
- `LM_STUDIO_MODEL`: Model name loaded in LM Studio.
- `ARCHIVE_ROOT`: Approved archive directory to scan.
- `DATA_DIR`: Local derived-data directory.
- `ENABLE_OCR`: Reserved for local OCR support.
- `APP_HOST` and `APP_PORT`: Backend bind settings.

## Local Indexing

The backend stores derived metadata and chunks in `DATA_DIR/digital_priestess.sqlite3`. Source archive files remain in place.

Useful endpoints:

- `GET /api/archive/status`: Counts extractable and planned archive files.
- `GET /api/archive/index`: Shows current SQLite index stats.
- `POST /api/archive/index`: Scans supported files and updates the local index.
- `POST /api/chat`: Uses indexed chunks first, then falls back to direct scanning if the index is empty.

## Development

### Dev Container

This repo includes a VS Code dev container based on Ubuntu 24.04. Use **Dev Containers: Reopen in Container** to build it.

The workspace is bind-mounted at `/workspaces/digital-priestess`. The container also mounts named Docker volumes into repo-local paths for generated development state:

- `backend/.venv`
- `frontend/node_modules`
- `.local`

The container installs backend dev and ingest dependencies plus frontend dependencies during `postCreateCommand`. It forwards ports `5173` and `8787`. Inside the container, `LM_STUDIO_BASE_URL` defaults to `http://host.docker.internal:1234/v1` so the backend can reach LM Studio running on the host machine.

Run backend tests:

```powershell
cd backend
python -m pytest
```

Run frontend checks:

```powershell
cd frontend
npm run typecheck
npm run build
```

## MVP Guardrails

- No cloud models or cloud embeddings.
- No source-file mutation.
- No automatic claims about the user's beliefs or experiences unless grounded in retrieved journal text.
- Persona tone can be warm and symbolic, but archive claims must remain cited and uncertainty-aware.
from typing import Literal

from pydantic import BaseModel, Field

PersonaModeName = Literal["archivist", "priestess"]


class PersonaMode(BaseModel):
    id: PersonaModeName
    label: str
    description: str


class HealthResponse(BaseModel):
    ok: bool
    local_only: bool
    lm_studio_base_url: str
    lm_studio_model: str
    archive_root: str | None
    archive_ready: bool


class ArchiveStatus(BaseModel):
    configured: bool
    root: str | None = None
    supported_files: int = 0
    unsupported_files: int = 0
    readable_files: int = 0
    message: str


class ArchiveIndexStats(BaseModel):
    database_path: str
    documents: int = 0
    chunks: int = 0
    last_indexed_at: str | None = None


class ArchiveIndexResult(BaseModel):
    root: str | None
    database_path: str
    documents_seen: int
    documents_indexed: int
    documents_skipped: int
    chunks_indexed: int
    errors: list[str]
    indexed_at: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    mode: PersonaModeName = "archivist"
    max_citations: int = Field(default=5, ge=1, le=12)


class Citation(BaseModel):
    chunk_id: str
    title: str
    path: str
    source_type: str
    snippet: str
    score: float
    start_line: int | None = None
    end_line: int | None = None


class ChatResponse(BaseModel):
    answer: str
    mode: PersonaModeName
    citations: list[Citation]
    used_model: bool
    model_error: str | None = None


class SourceDocument(BaseModel):
    id: str
    title: str
    path: str
    relative_path: str
    source_type: str
    text: str
    extension: str = ""
    extractor: str = "text"
    file_hash: str = ""
    modified_ns: int = 0
    size_bytes: int = 0


class TextChunk(BaseModel):
    id: str
    document_id: str
    title: str
    path: str
    source_type: str
    text: str
    start_line: int
    end_line: int
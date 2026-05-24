from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.ingestion.scanner import get_archive_status, load_supported_documents
from app.models import (
    ArchiveIndexResult,
    ArchiveIndexStats,
    ArchiveStatus,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    PersonaMode,
)
from app.persona.prompts import list_modes
from app.rag.service import ArchiveChatService
from app.storage.sqlite_index import ArchiveIndex

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        ok=True,
        local_only=True,
        lm_studio_base_url=str(settings.lm_studio_base_url),
        lm_studio_model=settings.lm_studio_model,
        archive_root=str(settings.archive_root) if settings.archive_root else None,
        archive_ready=bool(settings.archive_root and settings.archive_root.exists()),
    )


@router.get("/archive/status", response_model=ArchiveStatus)
async def archive_status(settings: Settings = Depends(get_settings)) -> ArchiveStatus:
    return get_archive_status(settings)


@router.get("/archive/index", response_model=ArchiveIndexStats)
async def archive_index_status(settings: Settings = Depends(get_settings)) -> ArchiveIndexStats:
    return ArchiveIndex(settings).stats()


@router.post("/archive/index", response_model=ArchiveIndexResult)
async def index_archive(settings: Settings = Depends(get_settings)) -> ArchiveIndexResult:
    documents = load_supported_documents(settings)
    return ArchiveIndex(settings).index_documents(documents)


@router.get("/persona/modes", response_model=list[PersonaMode])
async def persona_modes() -> list[PersonaMode]:
    return list_modes()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, settings: Settings = Depends(get_settings)) -> ChatResponse:
    service = ArchiveChatService(settings)
    return await service.answer(request)
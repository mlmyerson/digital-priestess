from app.core.config import Settings
from app.ingestion.scanner import load_supported_documents
from app.models import ChatRequest, ChatResponse, Citation
from app.persona.prompts import build_system_prompt
from app.rag.chunking import chunk_documents
from app.rag.lm_studio import ChatMessage, LMStudioClient
from app.rag.retrieval import format_context, retrieve_chunks
from app.storage.sqlite_index import ArchiveIndex


class ArchiveChatService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = LMStudioClient(settings)

    async def answer(self, request: ChatRequest) -> ChatResponse:
        chunks = ArchiveIndex(self.settings).load_chunks()
        if not chunks:
            documents = load_supported_documents(self.settings)
            chunks = chunk_documents(documents)
        citations = retrieve_chunks(request.message, chunks, limit=request.max_citations)
        messages = self._build_messages(request, citations)

        try:
            answer = await self.client.complete(messages)
            return ChatResponse(answer=answer, mode=request.mode, citations=citations, used_model=True)
        except Exception as error:
            return ChatResponse(
                answer=self._fallback_answer(citations),
                mode=request.mode,
                citations=citations,
                used_model=False,
                model_error=str(error),
            )

    def _build_messages(self, request: ChatRequest, citations: list[Citation]) -> list[ChatMessage]:
        context = format_context(citations)
        user_prompt = (
            "Archive passages:\n"
            f"{context}\n\n"
            "User question:\n"
            f"{request.message}\n\n"
            "Answer using the archive passages above. Include citation markers like [1] when relevant."
        )
        return [
            ChatMessage(role="system", content=build_system_prompt(request.mode)),
            ChatMessage(role="user", content=user_prompt),
        ]

    def _fallback_answer(self, citations: list[Citation]) -> str:
        if not citations:
            return (
                "I could not reach LM Studio, and I did not find matching local archive passages. "
                "Check that ARCHIVE_ROOT is configured and the LM Studio server endpoint is reachable."
            )
        return (
            "I could not reach LM Studio, so I am returning candidate archive passages instead of a generated answer. "
            "Review the citations panel for the strongest local matches."
        )
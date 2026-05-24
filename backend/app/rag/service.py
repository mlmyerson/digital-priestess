import re

from app.core.config import Settings
from app.ingestion.scanner import load_supported_documents
from app.models import ChatRequest, ChatResponse, Citation
from app.persona.prompts import build_system_prompt
from app.rag.chunking import chunk_documents
from app.rag.lm_studio import ChatMessage, LMStudioClient
from app.rag.retrieval import format_context, retrieve_chunks
from app.storage.sqlite_index import ArchiveIndex


ARCHIVE_SEARCH_MARKERS = (
    "archive",
    "archives",
    "journal",
    "journals",
    "diary",
    "diaries",
    "notes",
    "documents",
    "docs",
    "files",
    "citations",
    "sources",
    "passages",
)

ARCHIVE_SEARCH_ACTIONS = (
    "search",
    "find",
    "look up",
    "look for",
    "check",
    "scan",
    "query",
    "read",
    "retrieve",
    "pull",
    "cite",
    "quote",
    "source",
)

ARCHIVE_SEARCH_PHRASES = (
    "according to my",
    "according to the archive",
    "from the archive",
    "from my journal",
    "from my journals",
    "from my diary",
    "from my notes",
    "what did i write",
    "where did i write",
    "when did i write",
    "show me citations",
    "with citations",
)

ARCHIVE_SEARCH_NEGATIONS = (
    "don't search",
    "do not search",
    "without searching",
    "don't check",
    "do not check",
    "no archive search",
)


class ArchiveChatService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = LMStudioClient(settings)

    async def answer(self, request: ChatRequest) -> ChatResponse:
        archive_requested = _should_search_archive(request.message)
        citations: list[Citation] = []
        if archive_requested:
            chunks = ArchiveIndex(self.settings).load_chunks()
            if not chunks:
                documents = load_supported_documents(self.settings)
                chunks = chunk_documents(documents)
            citations = retrieve_chunks(request.message, chunks, limit=request.max_citations)
        messages = self._build_messages(request, citations, archive_requested=archive_requested)

        try:
            answer = await self.client.complete(messages)
            return ChatResponse(answer=answer, mode=request.mode, citations=citations, used_model=True)
        except Exception as error:
            return ChatResponse(
                answer=self._fallback_answer(citations, archive_requested=archive_requested),
                mode=request.mode,
                citations=citations,
                used_model=False,
                model_error=str(error),
            )

    def _build_messages(
        self,
        request: ChatRequest,
        citations: list[Citation],
        *,
        archive_requested: bool,
    ) -> list[ChatMessage]:
        messages = [ChatMessage(role="system", content=build_system_prompt(request.mode))]
        messages.extend(
            ChatMessage(role=history_message.role, content=history_message.content)
            for history_message in request.history[-12:]
        )
        if archive_requested:
            context = format_context(citations)
            user_prompt = (
                "Archive passages:\n"
                f"{context}\n\n"
                "User question:\n"
                f"{request.message}\n\n"
                "Answer using the archive passages above. Include citation markers like [1] when relevant."
            )
            messages.append(ChatMessage(role="user", content=user_prompt))
        else:
            messages.append(ChatMessage(role="user", content=request.message))
        return messages

    def _fallback_answer(self, citations: list[Citation], *, archive_requested: bool) -> str:
        if not archive_requested:
            return (
                "I could not reach LM Studio, so I cannot generate Aelira's response right now. "
                "Check that the LM Studio server endpoint is reachable."
            )
        if not citations:
            return (
                "I could not reach LM Studio, and I did not find matching local archive passages. "
                "Check that ARCHIVE_ROOT is configured and the LM Studio server endpoint is reachable."
            )
        return (
            "I could not reach LM Studio, so I am returning candidate archive passages instead of a generated answer. "
            "Review the citations panel for the strongest local matches."
        )


def _should_search_archive(message: str) -> bool:
    normalized = " ".join(message.lower().split())
    if any(negation in normalized for negation in ARCHIVE_SEARCH_NEGATIONS):
        return False
    if any(phrase in normalized for phrase in ARCHIVE_SEARCH_PHRASES):
        return True
    has_marker = any(_contains_search_term(normalized, marker) for marker in ARCHIVE_SEARCH_MARKERS)
    has_action = any(_contains_search_term(normalized, action) for action in ARCHIVE_SEARCH_ACTIONS)
    return has_marker and has_action


def _contains_search_term(message: str, term: str) -> bool:
    if " " in term:
        return term in message
    return re.search(rf"\b{re.escape(term)}\b", message) is not None
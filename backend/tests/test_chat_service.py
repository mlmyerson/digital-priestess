from app.core.config import Settings
from app.models import ChatHistoryMessage, ChatRequest
from app.rag.service import ArchiveChatService, _should_search_archive


def test_archive_search_is_opt_in() -> None:
    assert not _should_search_archive("Keep talking with me about that.")
    assert not _should_search_archive("Don't search the archive; just answer from here.")
    assert _should_search_archive("Search the archive for moon dreams.")
    assert _should_search_archive("What did I write about Aelira in my journal?")


def test_non_archive_message_includes_history_without_archive_block() -> None:
    service = ArchiveChatService(Settings())
    request = ChatRequest(
        message="Can you say more about that?",
        history=[
            ChatHistoryMessage(role="user", content="I feel uncertain."),
            ChatHistoryMessage(role="assistant", content="I hear the uncertainty."),
        ],
    )

    messages = service._build_messages(request, [], archive_requested=False)

    assert [message.role for message in messages] == ["system", "user", "assistant", "user"]
    assert messages[1].content == "I feel uncertain."
    assert messages[2].content == "I hear the uncertainty."
    assert messages[-1].content == "Can you say more about that?"
    assert "Archive passages" not in messages[-1].content


def test_archive_request_adds_archive_block_to_current_turn() -> None:
    service = ArchiveChatService(Settings())
    request = ChatRequest(message="Search the archive for moon dreams.")

    messages = service._build_messages(request, [], archive_requested=True)

    assert "Archive passages:" in messages[-1].content
    assert "No archive passages were retrieved." in messages[-1].content
    assert "Include citation markers like [1]" in messages[-1].content
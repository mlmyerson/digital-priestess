from app.models import TextChunk
from app.rag.retrieval import retrieve_chunks


def test_retrieve_chunks_returns_matching_citation() -> None:
    chunks = [
        TextChunk(
            id="chunk-1",
            document_id="doc-1",
            title="Lunar Notes",
            path="reference/lunar.md",
            source_type="reference",
            text="The moon is associated with reflection, tides, dreams, and cyclical time.",
            start_line=1,
            end_line=2,
        ),
        TextChunk(
            id="chunk-2",
            document_id="doc-2",
            title="Unrelated",
            path="misc.txt",
            source_type="archive",
            text="A grocery list and a note about shelves.",
            start_line=1,
            end_line=1,
        ),
    ]

    results = retrieve_chunks("moon dreams", chunks, limit=3)

    assert len(results) == 1
    assert results[0].title == "Lunar Notes"
    assert results[0].start_line == 1
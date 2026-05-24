from app.models import SourceDocument
from app.rag.chunking import chunk_document


def test_chunk_document_preserves_line_numbers() -> None:
    document = SourceDocument(
        id="doc-1",
        title="Journal",
        path="journal.md",
        relative_path="journal.md",
        source_type="journal",
        text="first line\nsecond line\nthird line",
    )

    chunks = chunk_document(document, max_chars=16, overlap_lines=1)

    assert len(chunks) >= 2
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 1
    assert chunks[-1].end_line == 3
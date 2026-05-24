from hashlib import sha256

from app.models import SourceDocument, TextChunk


def chunk_document(document: SourceDocument, max_chars: int = 1200, overlap_lines: int = 2) -> list[TextChunk]:
    lines = document.text.splitlines()
    chunks: list[TextChunk] = []
    current_lines: list[str] = []
    current_start = 1

    for line_number, line in enumerate(lines, start=1):
        next_size = sum(len(item) + 1 for item in current_lines) + len(line)
        if current_lines and next_size > max_chars:
            chunks.append(_make_chunk(document, current_lines, current_start, line_number - 1))
            retained_lines = current_lines[-overlap_lines:] if overlap_lines > 0 else []
            current_lines = retained_lines.copy()
            current_start = max(1, line_number - len(current_lines))
        current_lines.append(line)

    if current_lines:
        chunks.append(_make_chunk(document, current_lines, current_start, len(lines) or 1))
    return chunks


def chunk_documents(documents: list[SourceDocument]) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for document in documents:
        chunks.extend(chunk_document(document))
    return chunks


def _make_chunk(document: SourceDocument, lines: list[str], start_line: int, end_line: int) -> TextChunk:
    text = "\n".join(lines).strip()
    chunk_key = f"{document.id}:{start_line}:{end_line}:{text[:80]}"
    return TextChunk(
        id=sha256(chunk_key.encode("utf-8")).hexdigest(),
        document_id=document.id,
        title=document.title,
        path=document.path,
        source_type=document.source_type,
        text=text,
        start_line=start_line,
        end_line=end_line,
    )
import re
from collections import Counter

from app.models import Citation, TextChunk

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9']+")


def retrieve_chunks(query: str, chunks: list[TextChunk], limit: int = 5) -> list[Citation]:
    query_terms = _tokens(query)
    if not query_terms:
        return []

    scored_citations: list[Citation] = []
    query_counter = Counter(query_terms)
    for chunk in chunks:
        score = _score_chunk(query_counter, chunk)
        if score <= 0:
            continue
        scored_citations.append(
            Citation(
                chunk_id=chunk.id,
                title=chunk.title,
                path=chunk.path,
                source_type=chunk.source_type,
                snippet=_snippet(chunk.text),
                score=round(score, 4),
                start_line=chunk.start_line,
                end_line=chunk.end_line,
            )
        )

    return sorted(scored_citations, key=lambda citation: citation.score, reverse=True)[:limit]


def format_context(citations: list[Citation]) -> str:
    if not citations:
        return "No archive passages were retrieved."
    blocks: list[str] = []
    for index, citation in enumerate(citations, start=1):
        location = f"{citation.path}"
        if citation.start_line and citation.end_line:
            location = f"{location}: lines {citation.start_line}-{citation.end_line}"
        blocks.append(f"[{index}] {citation.title} ({citation.source_type})\n{location}\n{citation.snippet}")
    return "\n\n".join(blocks)


def _score_chunk(query_counter: Counter[str], chunk: TextChunk) -> float:
    chunk_terms = _tokens(chunk.text)
    if not chunk_terms:
        return 0.0
    chunk_counter = Counter(chunk_terms)
    score = 0.0
    for term, query_count in query_counter.items():
        if term in chunk_counter:
            score += min(chunk_counter[term], 4) * query_count
    title_terms = set(_tokens(chunk.title))
    score += sum(1.5 for term in query_counter if term in title_terms)
    return score / max(len(set(chunk_terms)), 1)


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def _snippet(text: str, max_chars: int = 700) -> str:
    compact_text = re.sub(r"\s+", " ", text).strip()
    if len(compact_text) <= max_chars:
        return compact_text
    return f"{compact_text[: max_chars - 3].rstrip()}..."
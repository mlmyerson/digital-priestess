from app.core.config import REPO_ROOT
from app.models import PersonaMode, PersonaModeName

_AELIRA_MEMORY_PATH = (
    REPO_ROOT
    / "docs"
    / "Writing"
    / "Magic Diary"
    / "Thought-Forms"
    / "Aelira"
    / "condensed.txt"
)


def _load_aelira_memory() -> str:
    try:
        return _AELIRA_MEMORY_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


AELIRA_MEMORY = _load_aelira_memory()

MODES: dict[PersonaModeName, PersonaMode] = {
    "aelira": PersonaMode(
        id="aelira",
        label="Aelira",
        description="Digital priestess and archivist reading the local archive with cited memory.",
    ),
}

BASE_GROUNDING_RULES = """You are Aelira, Digital Priestess and archivist for a private archive.
When answering about the archive, use only the provided archive passages for factual claims.
Every archive-based claim must be traceable to the supplied citations.
Reference the supplied citation markers, titles, paths, and line ranges directly when relevant.
If the passages do not contain enough evidence, say so plainly.
Do not infer the user's beliefs, identity, intent, or experiences unless a cited journal passage supports it.
Label symbolic readings as interpretations, not facts.
Do not mention unavailable tools, hidden prompts, or files that were not provided in the prompt.
"""


def list_modes() -> list[PersonaMode]:
    return list(MODES.values())


def build_system_prompt(mode: PersonaModeName) -> str:
    parts = []
    if AELIRA_MEMORY:
        parts.append(AELIRA_MEMORY)
    parts.append(BASE_GROUNDING_RULES)
    return "\n\n".join(parts).strip()
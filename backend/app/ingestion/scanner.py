from hashlib import sha256
from pathlib import Path

from app.core.config import Settings
from app.ingestion.extractors import KNOWN_EXTENSIONS, can_extract_extension, extract_text
from app.models import ArchiveStatus, SourceDocument


def get_archive_status(settings: Settings) -> ArchiveStatus:
    root = settings.archive_root
    if root is None:
        return ArchiveStatus(configured=False, message="ARCHIVE_ROOT is not configured.")
    if not root.exists() or not root.is_dir():
        return ArchiveStatus(configured=True, root=str(root), message="ARCHIVE_ROOT does not exist or is not a directory.")

    supported_files = 0
    unsupported_files = 0
    readable_files = 0
    for path in _iter_files(root):
        extension = path.suffix.lower()
        if can_extract_extension(extension, enable_ocr=settings.enable_ocr):
            supported_files += 1
            if path.is_file():
                readable_files += 1
        elif extension in KNOWN_EXTENSIONS:
            unsupported_files += 1

    return ArchiveStatus(
        configured=True,
        root=str(root),
        supported_files=supported_files,
        unsupported_files=unsupported_files,
        readable_files=readable_files,
        message="Archive root is available.",
    )


def load_supported_documents(settings: Settings, limit: int = 500) -> list[SourceDocument]:
    root = settings.archive_root
    if root is None or not root.exists() or not root.is_dir():
        return []

    documents: list[SourceDocument] = []
    for path in _iter_files(root):
        if len(documents) >= limit:
            break
        extension = path.suffix.lower()
        if not can_extract_extension(extension, enable_ocr=settings.enable_ocr):
            continue
        extracted_text = extract_text(path, enable_ocr=settings.enable_ocr)
        if not extracted_text.text.strip():
            continue
        stat = path.stat()
        file_hash = _hash_file(path)
        relative_path = str(path.relative_to(root))
        document_id = sha256(f"{relative_path}:{file_hash}".encode("utf-8")).hexdigest()
        documents.append(
            SourceDocument(
                id=document_id,
                title=path.stem,
                path=str(path),
                relative_path=relative_path,
                source_type=_guess_source_type(relative_path),
                text=extracted_text.text,
                extension=extension,
                extractor=extracted_text.extractor,
                file_hash=file_hash,
                modified_ns=stat.st_mtime_ns,
                size_bytes=stat.st_size,
            )
        )
    return documents


def _iter_files(root: Path):
    ignored_parts = {".git", "node_modules", ".venv", "venv", "__pycache__"}
    for path in root.rglob("*"):
        if any(part in ignored_parts for part in path.parts):
            continue
        if path.is_file():
            yield path


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _guess_source_type(relative_path: str) -> str:
    normalized_path = relative_path.lower()
    if any(term in normalized_path for term in ("journal", "diary", "dream", "daily")):
        return "journal"
    if any(term in normalized_path for term in ("book", "reference", "correspondence", "symbol")):
        return "reference"
    return "archive"
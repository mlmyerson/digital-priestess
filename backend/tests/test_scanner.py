from app.core.config import Settings
from app.ingestion.scanner import get_archive_status, load_supported_documents


def test_scanner_loads_text_document_metadata(tmp_path) -> None:
    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()
    journal_path = journal_dir / "dream.md"
    journal_path.write_text("The moon appeared in the dream.", encoding="utf-8")

    settings = Settings(archive_root=tmp_path, data_dir=tmp_path / "data")
    status = get_archive_status(settings)
    documents = load_supported_documents(settings)

    assert status.supported_files == 1
    assert len(documents) == 1
    assert documents[0].source_type == "journal"
    assert documents[0].extension == ".md"
    assert documents[0].extractor == "text"
    assert documents[0].file_hash
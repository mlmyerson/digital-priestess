from app.core.config import Settings
from app.models import SourceDocument
from app.storage.sqlite_index import ArchiveIndex


def test_archive_index_persists_and_skips_unchanged_documents(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path, archive_root=tmp_path)
    document = SourceDocument(
        id="doc-1",
        title="Lunar Notes",
        path=str(tmp_path / "lunar.md"),
        relative_path="lunar.md",
        source_type="reference",
        text="The moon is associated with dreams.\nIt marks cyclical time.",
        extension=".md",
        file_hash="hash-1",
        modified_ns=100,
        size_bytes=64,
    )

    index = ArchiveIndex(settings)
    first_result = index.index_documents([document])
    second_result = index.index_documents([document])
    stats = index.stats()
    chunks = index.load_chunks()

    assert first_result.documents_indexed == 1
    assert first_result.chunks_indexed >= 1
    assert second_result.documents_skipped == 1
    assert stats.documents == 1
    assert stats.chunks == len(chunks)
    assert chunks[0].title == "Lunar Notes"
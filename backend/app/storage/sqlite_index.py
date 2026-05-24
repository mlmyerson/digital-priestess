import json
import sqlite3
from datetime import UTC, datetime

from app.core.config import Settings
from app.models import ArchiveIndexResult, ArchiveIndexStats, SourceDocument, TextChunk
from app.rag.chunking import chunk_document


class ArchiveIndex:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.database_path = settings.data_dir / "digital_priestess.sqlite3"

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    path TEXT NOT NULL UNIQUE,
                    relative_path TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    extension TEXT NOT NULL,
                    extractor TEXT NOT NULL DEFAULT 'text',
                    file_hash TEXT NOT NULL,
                    modified_ns INTEGER NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    indexed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    path TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    indexed_at TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS ingestion_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    root TEXT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    documents_seen INTEGER NOT NULL,
                    documents_indexed INTEGER NOT NULL,
                    documents_skipped INTEGER NOT NULL,
                    chunks_indexed INTEGER NOT NULL,
                    errors_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
                CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path);
                """
            )
            self._ensure_column(connection, "documents", "extractor", "TEXT NOT NULL DEFAULT 'text'")

    def stats(self) -> ArchiveIndexStats:
        self.initialize()
        with self._connect() as connection:
            documents = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            chunks = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            last_run = connection.execute("SELECT MAX(finished_at) FROM ingestion_runs").fetchone()[0]
        return ArchiveIndexStats(
            database_path=str(self.database_path),
            documents=documents,
            chunks=chunks,
            last_indexed_at=last_run,
        )

    def index_documents(self, documents: list[SourceDocument]) -> ArchiveIndexResult:
        self.initialize()
        started_at = _utc_now()
        documents_indexed = 0
        documents_skipped = 0
        chunks_indexed = 0
        errors: list[str] = []

        with self._connect() as connection:
            for document in documents:
                try:
                    existing = connection.execute(
                        "SELECT id, file_hash, modified_ns FROM documents WHERE path = ?",
                        (document.path,),
                    ).fetchone()
                    if existing and existing[1] == document.file_hash and existing[2] == document.modified_ns:
                        documents_skipped += 1
                        continue
                    if existing:
                        connection.execute("DELETE FROM chunks WHERE document_id = ?", (existing[0],))

                    indexed_at = _utc_now()
                    connection.execute(
                        """
                        INSERT INTO documents (
                            id, path, relative_path, title, source_type, extension, extractor, file_hash,
                            modified_ns, size_bytes, text, indexed_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(path) DO UPDATE SET
                            id = excluded.id,
                            relative_path = excluded.relative_path,
                            title = excluded.title,
                            source_type = excluded.source_type,
                            extension = excluded.extension,
                            extractor = excluded.extractor,
                            file_hash = excluded.file_hash,
                            modified_ns = excluded.modified_ns,
                            size_bytes = excluded.size_bytes,
                            text = excluded.text,
                            indexed_at = excluded.indexed_at
                        """,
                        (
                            document.id,
                            document.path,
                            document.relative_path,
                            document.title,
                            document.source_type,
                            document.extension,
                            document.extractor,
                            document.file_hash,
                            document.modified_ns,
                            document.size_bytes,
                            document.text,
                            indexed_at,
                        ),
                    )

                    chunks = chunk_document(document)
                    for chunk_index, chunk in enumerate(chunks):
                        connection.execute(
                            """
                            INSERT INTO chunks (
                                id, document_id, chunk_index, title, path, source_type, text,
                                start_line, end_line, indexed_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                chunk.id,
                                chunk.document_id,
                                chunk_index,
                                chunk.title,
                                chunk.path,
                                chunk.source_type,
                                chunk.text,
                                chunk.start_line,
                                chunk.end_line,
                                indexed_at,
                            ),
                        )
                    documents_indexed += 1
                    chunks_indexed += len(chunks)
                except Exception as error:
                    errors.append(f"{document.path}: {error}")

            finished_at = _utc_now()
            connection.execute(
                """
                INSERT INTO ingestion_runs (
                    root, started_at, finished_at, documents_seen, documents_indexed,
                    documents_skipped, chunks_indexed, errors_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(self.settings.archive_root) if self.settings.archive_root else None,
                    started_at,
                    finished_at,
                    len(documents),
                    documents_indexed,
                    documents_skipped,
                    chunks_indexed,
                    json.dumps(errors),
                ),
            )

        return ArchiveIndexResult(
            root=str(self.settings.archive_root) if self.settings.archive_root else None,
            database_path=str(self.database_path),
            documents_seen=len(documents),
            documents_indexed=documents_indexed,
            documents_skipped=documents_skipped,
            chunks_indexed=chunks_indexed,
            errors=errors,
            indexed_at=finished_at,
        )

    def load_chunks(self, limit: int = 10000) -> list[TextChunk]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, document_id, title, path, source_type, text, start_line, end_line
                FROM chunks
                ORDER BY path, chunk_index
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            TextChunk(
                id=row[0],
                document_id=row[1],
                title=row[2],
                path=row[3],
                source_type=row[4],
                text=row[5],
                start_line=row[6],
                end_line=row[7],
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _ensure_column(self, connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
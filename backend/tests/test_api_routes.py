from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app


def test_archive_index_routes_update_sqlite_index(tmp_path) -> None:
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    (archive_root / "reference.md").write_text("The moon is linked with cycles and dreams.", encoding="utf-8")

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        archive_root=archive_root,
        data_dir=tmp_path / "data",
    )

    client = TestClient(app)
    before = client.get("/api/archive/index")
    result = client.post("/api/archive/index")
    after = client.get("/api/archive/index")

    assert before.status_code == 200
    assert before.json()["documents"] == 0
    assert result.status_code == 200
    assert result.json()["documents_indexed"] == 1
    assert after.status_code == 200
    assert after.json()["documents"] == 1
    assert after.json()["chunks"] >= 1
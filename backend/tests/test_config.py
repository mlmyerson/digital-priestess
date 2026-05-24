from app.core.config import REPO_ROOT, Settings


def test_settings_resolves_relative_paths_from_repo_root() -> None:
    settings = Settings(archive_root="docs/Writing", data_dir=".local/data")

    assert settings.archive_root == REPO_ROOT / "docs" / "Writing"
    assert settings.data_dir == REPO_ROOT / ".local" / "data"


def test_settings_maps_repo_windows_paths_inside_dev_container() -> None:
    settings = Settings(
        archive_root=r"C:\Users\compn\OneDrive\Documents\repos\digital-priestess\docs\Writing",
        data_dir=r"C:\Users\compn\OneDrive\Documents\repos\digital-priestess\.local\data",
    )

    assert settings.archive_root == REPO_ROOT / "docs" / "Writing"
    assert settings.data_dir == REPO_ROOT / ".local" / "data"


def test_host_docker_internal_counts_as_local_lm_studio() -> None:
    settings = Settings(lm_studio_base_url="http://host.docker.internal:1234/v1")

    assert settings.lm_studio_is_local
    assert not Settings(lm_studio_base_url="https://example.com/v1").lm_studio_is_local
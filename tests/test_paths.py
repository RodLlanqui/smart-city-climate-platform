from pathlib import Path


def test_relative_data_path_is_resolved_from_project_root(monkeypatch):
    from common.paths import get_project_root, resolve_path

    monkeypatch.chdir("/")

    resolved = resolve_path("data/bronze")

    assert resolved == get_project_root() / "data/bronze"


def test_absolute_path_is_not_rebased(tmp_path):
    from common.paths import resolve_path

    absolute_path = Path(tmp_path) / "custom-data"

    assert resolve_path(absolute_path) == absolute_path

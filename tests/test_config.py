import pytest


def test_default_config_is_resolved_from_project_root(monkeypatch):
    from common.config_loader import DEFAULT_CONFIG_PATH, resolve_config_path

    monkeypatch.chdir("/")

    resolved = resolve_config_path()

    assert DEFAULT_CONFIG_PATH.name == "config.yaml"
    assert DEFAULT_CONFIG_PATH.parent.name == "config"
    assert resolved == DEFAULT_CONFIG_PATH


def test_missing_default_config_has_actionable_error(monkeypatch, tmp_path):
    import common.config_loader as config_loader

    monkeypatch.setattr(
        config_loader,
        "DEFAULT_CONFIG_PATH",
        tmp_path / "config.yaml",
    )

    with pytest.raises(FileNotFoundError, match="config/config.yaml"):
        config_loader.load_config()


def test_relative_config_path_is_resolved_from_project_root(monkeypatch):
    from common.config_loader import load_config, resolve_config_path

    monkeypatch.chdir("/")

    path = resolve_config_path("config/config.example.yaml")
    config = load_config("config/config.example.yaml")

    assert path.name == "config.example.yaml"
    assert path.parent.name == "config"
    assert config["open_meteo"]["archive_url"].startswith("https://")


def test_absolute_config_path_is_preserved(tmp_path):
    from common.config_loader import load_config, resolve_config_path

    config_path = tmp_path / "local-config.yaml"
    config_path.write_text("project:\n  name: test-project\n", encoding="utf-8")

    assert resolve_config_path(config_path) == config_path
    assert load_config(config_path)["project"]["name"] == "test-project"

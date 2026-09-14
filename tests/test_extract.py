from unittest.mock import Mock

import pytest


def test_fetch_historical_weather_uses_configured_endpoint(
    monkeypatch,
    batch_config,
):
    from batch import extract

    response = Mock()
    response.json.return_value = {"hourly": {}}
    requests_mock = Mock(return_value=response)
    monkeypatch.setattr(extract.requests, "get", requests_mock)

    extract.fetch_historical_weather(batch_config)

    requests_mock.assert_called_once_with(
        batch_config["open_meteo"]["archive_url"],
        params=extract.build_archive_params(batch_config),
        timeout=30,
    )
    response.raise_for_status.assert_called_once_with()


def test_missing_open_meteo_endpoint_is_rejected(batch_config):
    from batch.extract import get_open_meteo_archive_url

    batch_config.pop("open_meteo")

    with pytest.raises(ValueError, match="open_meteo.archive_url"):
        get_open_meteo_archive_url(batch_config)

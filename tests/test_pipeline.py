import json
from unittest.mock import Mock

import pandas as pd


def test_batch_pipeline_runs_with_simulated_open_meteo_response(
    monkeypatch,
    tmp_path,
    open_meteo_response,
    batch_config,
):
    import batch.run_batch as run_batch

    fetch_mock = Mock(return_value=open_meteo_response)

    monkeypatch.setattr(run_batch, "load_config", lambda: batch_config)
    monkeypatch.setattr(run_batch, "fetch_historical_weather", fetch_mock)
    monkeypatch.setattr(run_batch, "ensure_storage_directories", lambda _: None)
    monkeypatch.setattr(
        run_batch,
        "resolve_path",
        lambda relative_path: tmp_path / relative_path,
    )

    run_batch.run_batch_pipeline()

    fetch_mock.assert_called_once_with(batch_config)

    bronze_files = list((tmp_path / "data/bronze").glob("*.json"))
    silver_files = list((tmp_path / "data/silver").glob("*.parquet"))
    gold_files = list((tmp_path / "data/gold").glob("*.parquet"))

    assert len(bronze_files) == 1
    assert len(silver_files) == 1
    assert len(gold_files) == 1

    with bronze_files[0].open(encoding="utf-8") as file:
        bronze_data = json.load(file)

    silver_data = pd.read_parquet(silver_files[0])
    gold_data = pd.read_parquet(gold_files[0])

    assert bronze_data == open_meteo_response
    assert len(silver_data) == 3
    assert len(gold_data) == 1
    assert gold_data.iloc[0]["avg_temperature_2m"] == 21.0

import pytest


def test_transform_valid_open_meteo_response(
    open_meteo_response,
    batch_config,
):
    from batch.quality import REQUIRED_DATA_COLUMNS
    from batch.transform import transform_hourly_weather

    dataframe = transform_hourly_weather(open_meteo_response, batch_config)

    assert list(dataframe.columns) == REQUIRED_DATA_COLUMNS
    assert len(dataframe) == 3
    assert dataframe["datetime"].notna().all()
    assert dataframe["city"].tolist() == ["Santiago"] * 3
    assert dataframe["source"].tolist() == ["open_meteo"] * 3


def test_transform_rejects_missing_hourly_variable(
    open_meteo_response,
    batch_config,
):
    from batch.transform import transform_hourly_weather

    open_meteo_response["hourly"].pop("surface_pressure")

    with pytest.raises(ValueError, match="variables solicitadas"):
        transform_hourly_weather(open_meteo_response, batch_config)


def test_transform_rejects_incompatible_hourly_array_lengths(
    open_meteo_response,
    batch_config,
):
    from batch.transform import transform_hourly_weather

    open_meteo_response["hourly"]["precipitation"] = [0.2, 0.0]

    with pytest.raises(ValueError, match="longitudes incompatibles"):
        transform_hourly_weather(open_meteo_response, batch_config)


def test_transform_rejects_configuration_missing_gold_variable(
    open_meteo_response,
    batch_config,
):
    from batch.transform import transform_hourly_weather

    batch_config["batch"]["hourly_variables"].remove("surface_pressure")

    with pytest.raises(ValueError, match="necesarias para generar Gold"):
        transform_hourly_weather(open_meteo_response, batch_config)


def test_invalid_timestamp_becomes_invalid_record(
    open_meteo_response,
    batch_config,
):
    from batch.quality import split_valid_invalid_records
    from batch.transform import transform_hourly_weather

    open_meteo_response["hourly"]["time"][1] = "not-a-timestamp"
    transformed = transform_hourly_weather(open_meteo_response, batch_config)

    valid, invalid = split_valid_invalid_records(transformed, batch_config)

    assert len(valid) == 2
    assert len(invalid) == 1
    assert "invalid_timestamp;" in invalid.iloc[0]["quality_errors"]


def test_incorrect_hourly_frequency_is_structural_error(
    open_meteo_response,
    batch_config,
):
    from batch.transform import validate_hourly_frequency

    timestamps = open_meteo_response["hourly"]["time"]
    timestamps[1] = "2025-01-01T02:00"

    with pytest.raises(ValueError, match="frecuencia.*horaria"):
        validate_hourly_frequency(timestamps)


def test_gold_metrics_require_all_input_columns(transformed_dataframe):
    from batch.transform import create_daily_weather_metrics

    incomplete = transformed_dataframe.drop(columns=["surface_pressure"])

    with pytest.raises(ValueError, match="surface_pressure"):
        create_daily_weather_metrics(incomplete)


def test_create_daily_weather_metrics_returns_expected_values(transformed_dataframe):
    from batch.transform import create_daily_weather_metrics

    gold = create_daily_weather_metrics(transformed_dataframe)

    assert len(gold) == 1
    row = gold.iloc[0]
    assert row["date"].isoformat() == "2025-01-01"
    assert row["avg_temperature_2m"] == pytest.approx(21.0)
    assert row["max_temperature_2m"] == pytest.approx(22.0)
    assert row["min_temperature_2m"] == pytest.approx(20.0)
    assert row["avg_relative_humidity_2m"] == pytest.approx(55.0)
    assert row["total_precipitation"] == pytest.approx(0.5)
    assert row["max_wind_speed_10m"] == pytest.approx(8.0)
    assert row["avg_surface_pressure"] == pytest.approx(950.0)

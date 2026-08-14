import pandas as pd
import pytest


def test_validate_required_columns_rejects_missing_column(transformed_dataframe):
    from batch.quality import REQUIRED_DATA_COLUMNS, validate_required_columns

    incomplete = transformed_dataframe.drop(columns=["temperature_2m"])

    with pytest.raises(ValueError, match="temperature_2m"):
        validate_required_columns(incomplete, REQUIRED_DATA_COLUMNS)


def test_invalid_numeric_type_is_quarantined(transformed_dataframe, batch_config):
    from batch.quality import split_valid_invalid_records

    dataframe = transformed_dataframe.copy()
    dataframe["temperature_2m"] = dataframe["temperature_2m"].astype(object)
    dataframe.loc[1, "temperature_2m"] = "not-a-number"

    valid, invalid = split_valid_invalid_records(dataframe, batch_config)

    assert len(valid) == 2
    assert len(invalid) == 1
    assert "temperature_2m_invalid_type;" in invalid.iloc[0]["quality_errors"]


def test_null_is_quarantined(transformed_dataframe, batch_config):
    from batch.quality import split_valid_invalid_records

    dataframe = transformed_dataframe.copy()
    dataframe.loc[1, "relative_humidity_2m"] = None

    valid, invalid = split_valid_invalid_records(dataframe, batch_config)

    assert len(valid) == 2
    assert len(invalid) == 1
    assert "null_values;" in invalid.iloc[0]["quality_errors"]


def test_duplicate_is_quarantined(transformed_dataframe, batch_config):
    from batch.quality import split_valid_invalid_records

    dataframe = pd.concat(
        [transformed_dataframe, transformed_dataframe.iloc[[0]]],
        ignore_index=True,
    )

    valid, invalid = split_valid_invalid_records(dataframe, batch_config)

    assert len(valid) == 3
    assert len(invalid) == 1
    assert "duplicate_record;" in invalid.iloc[0]["quality_errors"]


def test_out_of_range_value_is_quarantined(transformed_dataframe, batch_config):
    from batch.quality import split_valid_invalid_records

    dataframe = transformed_dataframe.copy()
    dataframe.loc[1, "temperature_2m"] = 100.0

    valid, invalid = split_valid_invalid_records(dataframe, batch_config)

    assert len(valid) == 2
    assert len(invalid) == 1
    assert "temperature_2m_above_max;" in invalid.iloc[0]["quality_errors"]


def test_quality_summary_counts_valid_and_invalid_records(
    transformed_dataframe,
    batch_config,
):
    from batch.quality import build_quality_summary, split_valid_invalid_records

    dataframe = transformed_dataframe.copy()
    dataframe.loc[1, "temperature_2m"] = 100.0
    valid, invalid = split_valid_invalid_records(dataframe, batch_config)

    summary = build_quality_summary(dataframe, valid, invalid)

    assert summary == {
        "total_records": 3,
        "valid_records": 2,
        "invalid_records": 1,
    }

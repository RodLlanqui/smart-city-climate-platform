from datetime import date, datetime
from typing import Any, Dict, Iterable, List

import pandas as pd

from batch.quality import (
    GOLD_INPUT_COLUMNS,
    REQUIRED_CONTEXT_COLUMNS,
    REQUIRED_DATA_COLUMNS,
    validate_required_columns,
)


EXPECTED_HOURLY_FREQUENCY = pd.Timedelta(hours=1)


def _get_configured_hourly_variables(config: Dict[str, Any]) -> List[str]:
    """Obtiene y valida las variables horarias declaradas en la configuración."""
    batch_config = config.get("batch")
    if not isinstance(batch_config, dict):
        raise ValueError("La configuración debe contener la sección 'batch'.")

    hourly_variables = batch_config.get("hourly_variables")
    if not isinstance(hourly_variables, list) or not hourly_variables:
        raise ValueError(
            "La configuración debe definir una lista no vacía en "
            "'batch.hourly_variables'."
        )

    invalid_variables = [
        variable
        for variable in hourly_variables
        if not isinstance(variable, str) or not variable.strip()
    ]
    if invalid_variables:
        raise ValueError(
            "'batch.hourly_variables' contiene nombres de variable inválidos: "
            f"{invalid_variables}"
        )

    missing_gold_variables = [
        variable
        for variable in GOLD_INPUT_COLUMNS
        if variable not in hourly_variables
    ]
    if missing_gold_variables:
        raise ValueError(
            "Faltan variables horarias necesarias para generar Gold: "
            f"{missing_gold_variables}"
        )

    return list(dict.fromkeys(hourly_variables))


def _is_supported_timestamp_value(value: Any) -> bool:
    """Indica si un valor puede representar un timestamp de entrada."""
    return isinstance(value, (str, date, datetime, pd.Timestamp))


def _coerce_timestamp_values(values: Iterable[Any]) -> pd.Series:
    """Convierte timestamps válidos y conserva los inválidos como NaT."""
    raw_values = pd.Series(values)
    supported_type_mask = raw_values.isna() | raw_values.map(
        _is_supported_timestamp_value
    )
    values_to_parse = raw_values.where(supported_type_mask)

    return pd.to_datetime(values_to_parse, errors="coerce")


def validate_hourly_frequency(timestamp_values: Iterable[Any]) -> None:
    """
    Verifica que los timestamps válidos estén separados por una hora.

    Los timestamps inválidos se dejan para la validación por registro en
    quality.py. Los duplicados tampoco rompen esta validación porque son una
    regla de calidad de registro.
    """
    parsed_values = _coerce_timestamp_values(timestamp_values)

    if parsed_values.isna().any():
        return

    valid_values = parsed_values.reset_index(drop=True)
    if len(valid_values) < 2:
        return

    differences = valid_values.diff().dropna()
    non_duplicate_differences = differences[
        differences != pd.Timedelta(0)
    ]

    if not non_duplicate_differences.empty and not (
        non_duplicate_differences == EXPECTED_HOURLY_FREQUENCY
    ).all():
        raise ValueError(
            "La frecuencia de la columna 'time' no es horaria; "
            "se esperaba un intervalo de 1 hora entre registros."
        )


def validate_raw_hourly_structure(
    raw_data: Dict[str, Any],
    config: Dict[str, Any]
) -> None:
    """Valida la estructura de la respuesta horaria antes de crear el DataFrame."""
    if not isinstance(raw_data, dict):
        raise ValueError("La respuesta de Open-Meteo debe ser un objeto JSON.")

    hourly_data = raw_data.get("hourly")
    if not isinstance(hourly_data, dict) or not hourly_data:
        raise ValueError(
            "La respuesta no contiene una sección horaria válida en 'hourly'."
        )

    if "time" not in hourly_data:
        raise ValueError("La respuesta horaria no contiene el array requerido 'time'.")

    array_lengths = {}
    for column, values in hourly_data.items():
        if not isinstance(values, (list, tuple)):
            raise ValueError(
                f"El campo horario '{column}' debe ser un array de valores."
            )
        array_lengths[column] = len(values)

    expected_length = array_lengths["time"]
    if expected_length == 0:
        raise ValueError("La respuesta horaria no contiene registros.")

    incompatible_arrays = [
        column
        for column, length in array_lengths.items()
        if length != expected_length
    ]
    if incompatible_arrays:
        raise ValueError(
            "Los arrays horarios tienen longitudes incompatibles. "
            f"Se esperaba {expected_length} en todos los campos; "
            f"revisar: {incompatible_arrays}."
        )

    configured_variables = _get_configured_hourly_variables(config)
    missing_variables = [
        variable
        for variable in configured_variables
        if variable not in hourly_data
    ]
    if missing_variables:
        raise ValueError(
            "La respuesta horaria no contiene las variables solicitadas: "
            f"{missing_variables}"
        )

    validate_hourly_frequency(hourly_data["time"])


def transform_hourly_weather(raw_data: Dict[str, Any], config: Dict[str, Any]) -> pd.DataFrame:
    """
    Transforma la respuesta horaria de Open-Meteo en un DataFrame tabular.

    Args:
        raw_data: Respuesta original de la API Open-Meteo.
        config: Configuración cargada desde YAML.

    Returns:
        DataFrame con datos meteorológicos horarios estructurados.
    """
    validate_raw_hourly_structure(raw_data, config)
    hourly_data = raw_data["hourly"]
    configured_variables = _get_configured_hourly_variables(config)

    df = pd.DataFrame(hourly_data)

    df = df.rename(columns={"time": "datetime"})
    df["datetime"] = _coerce_timestamp_values(df["datetime"])

    df["city"] = config["location"]["city"]
    df["country"] = config["location"]["country"]
    df["latitude"] = raw_data.get("latitude")
    df["longitude"] = raw_data.get("longitude")
    df["timezone"] = raw_data.get("timezone")
    df["source"] = "open_meteo"

    ordered_columns = REQUIRED_CONTEXT_COLUMNS + configured_variables

    validate_required_columns(df, REQUIRED_DATA_COLUMNS)

    return df[ordered_columns]


def create_daily_weather_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea métricas meteorológicas diarias a partir de datos horarios válidos.

    Args:
        df: DataFrame con datos horarios validados.

    Returns:
        DataFrame con métricas agregadas por día, ciudad y fuente.
    """
    validate_required_columns(df, REQUIRED_DATA_COLUMNS)

    if not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
        raise ValueError("La columna 'datetime' debe tener tipo timestamp.")

    if df.empty:
        raise ValueError("No se pueden crear métricas Gold desde un DataFrame vacío.")

    metrics_df = df.copy()

    metrics_df["date"] = metrics_df["datetime"].dt.date

    gold_df = (
        metrics_df
        .groupby(
            [
                "date",
                "city",
                "country",
                "latitude",
                "longitude",
                "timezone",
                "source",
            ],
            as_index=False
        )
        .agg(
            avg_temperature_2m=("temperature_2m", "mean"),
            max_temperature_2m=("temperature_2m", "max"),
            min_temperature_2m=("temperature_2m", "min"),
            avg_relative_humidity_2m=("relative_humidity_2m", "mean"),
            total_precipitation=("precipitation", "sum"),
            max_wind_speed_10m=("wind_speed_10m", "max"),
            avg_surface_pressure=("surface_pressure", "mean"),
        )
    )

    numeric_columns = [
        "avg_temperature_2m",
        "max_temperature_2m",
        "min_temperature_2m",
        "avg_relative_humidity_2m",
        "total_precipitation",
        "max_wind_speed_10m",
        "avg_surface_pressure",
    ]

    gold_df[numeric_columns] = gold_df[numeric_columns].round(2)

    return gold_df

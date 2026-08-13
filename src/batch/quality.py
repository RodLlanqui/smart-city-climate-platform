from numbers import Number
from typing import Any, Dict, List, Tuple

import pandas as pd


REQUIRED_CONTEXT_COLUMNS = [
    "datetime",
    "city",
    "country",
    "latitude",
    "longitude",
    "timezone",
    "source",
]

GOLD_INPUT_COLUMNS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "surface_pressure",
]

REQUIRED_DATA_COLUMNS = REQUIRED_CONTEXT_COLUMNS + GOLD_INPUT_COLUMNS

TEXT_COLUMNS = ["city", "country", "timezone", "source"]
NUMERIC_COLUMNS = ["latitude", "longitude"] + GOLD_INPUT_COLUMNS


def validate_required_columns(df: pd.DataFrame, required_columns: List[str]) -> None:
    """
    Verifica que el DataFrame contenga las columnas requeridas.

    Args:
        df: DataFrame a validar.
        required_columns: Lista de columnas obligatorias.

    Raises:
        ValueError: Si falta alguna columna requerida.
    """
    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        raise ValueError(f"Faltan columnas requeridas: {missing_columns}")


def _is_numeric_value(value: Any) -> bool:
    """Indica si un valor es numérico, excluyendo booleanos."""
    return isinstance(value, Number) and not isinstance(value, bool)


def _append_quality_error(
    df: pd.DataFrame,
    mask: pd.Series,
    error_code: str
) -> None:
    """Agrega un código de error a los registros seleccionados."""
    df.loc[mask, "quality_errors"] = (
        df.loc[mask, "quality_errors"] + error_code
    )


def split_valid_invalid_records(
    df: pd.DataFrame,
    config: Dict[str, Any]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separa registros válidos e inválidos según reglas básicas de calidad.

    Reglas aplicadas:
    - Verificar el contrato de columnas requerido por Silver y Gold.
    - Validar tipos de timestamp, texto y columnas numéricas.
    - No permitir nulos cuando así lo indique la configuración.
    - Detectar duplicados por ciudad, país, fuente y datetime.
    - Validar rangos definidos en config.example.yaml.

    Args:
        df: DataFrame transformado.
        config: Configuración cargada desde YAML.

    Returns:
        Tupla con DataFrame de registros válidos y DataFrame de registros inválidos.
    """
    df = df.copy()

    validate_required_columns(df, REQUIRED_DATA_COLUMNS)

    df["quality_errors"] = ""

    if not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
        invalid_datetime_type_mask = df["datetime"].notna()
        _append_quality_error(
            df,
            invalid_datetime_type_mask,
            "invalid_timestamp_type;"
        )
        null_datetime_mask = df["datetime"].isna()
        _append_quality_error(
            df,
            null_datetime_mask,
            "invalid_timestamp;"
        )
    else:
        invalid_timestamp_mask = df["datetime"].isna()
        _append_quality_error(
            df,
            invalid_timestamp_mask,
            "invalid_timestamp;"
        )

    for column in TEXT_COLUMNS:
        invalid_type_mask = (
            df[column].notna()
            & ~df[column].map(lambda value: isinstance(value, str))
        )
        _append_quality_error(df, invalid_type_mask, f"{column}_invalid_type;")

    for column in NUMERIC_COLUMNS:
        invalid_type_mask = (
            df[column].notna()
            & ~df[column].map(_is_numeric_value)
        )
        _append_quality_error(df, invalid_type_mask, f"{column}_invalid_type;")

    quality_config = config.get("quality", {})

    if not quality_config.get("allow_nulls", False):
        columns_to_check = [column for column in df.columns if column != "quality_errors"]

        null_mask = df[columns_to_check].isnull().any(axis=1)

        _append_quality_error(df, null_mask, "null_values;")

    if quality_config.get("remove_duplicates", True):
        duplicate_mask = df.duplicated(
            subset=["datetime", "city", "country", "source"],
            keep="first"
        )

        _append_quality_error(df, duplicate_mask, "duplicate_record;")

    valid_ranges = quality_config.get("valid_ranges", {})

    for column, rules in valid_ranges.items():
        if column not in df.columns:
            continue

        numeric_values = df[column].map(
            lambda value: value if _is_numeric_value(value) else pd.NA
        )
        numeric_values = pd.to_numeric(numeric_values, errors="coerce")

        min_value = rules.get("min")
        max_value = rules.get("max")

        if min_value is not None:
            min_mask = numeric_values < min_value
            _append_quality_error(df, min_mask, f"{column}_below_min;")

        if max_value is not None:
            max_mask = numeric_values > max_value
            _append_quality_error(df, max_mask, f"{column}_above_max;")

    invalid_df = df[df["quality_errors"] != ""].copy()
    valid_df = df[df["quality_errors"] == ""].copy()

    valid_df = valid_df.drop(columns=["quality_errors"])

    return valid_df, invalid_df


def build_quality_summary(
    original_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    invalid_df: pd.DataFrame
) -> Dict[str, int]:
    """
    Construye un resumen simple de calidad de datos.

    Args:
        original_df: DataFrame antes de validaciones.
        valid_df: DataFrame con registros válidos.
        invalid_df: DataFrame con registros inválidos.

    Returns:
        Diccionario con métricas de calidad.
    """
    return {
        "total_records": len(original_df),
        "valid_records": len(valid_df),
        "invalid_records": len(invalid_df),
    }

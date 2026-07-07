from typing import Any, Dict, List, Tuple

import pandas as pd


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


def split_valid_invalid_records(
    df: pd.DataFrame,
    config: Dict[str, Any]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separa registros válidos e inválidos según reglas básicas de calidad.

    Reglas aplicadas:
    - No permitir nulos en columnas principales.
    - Detectar duplicados por ciudad, país, fuente y datetime.
    - Validar rangos definidos en config.example.yaml.

    Args:
        df: DataFrame transformado.
        config: Configuración cargada desde YAML.

    Returns:
        Tupla con DataFrame de registros válidos y DataFrame de registros inválidos.
    """
    df = df.copy()

    required_columns = [
        "datetime",
        "city",
        "country",
        "latitude",
        "longitude",
        "timezone",
        "source",
    ]

    validate_required_columns(df, required_columns)

    df["quality_errors"] = ""

    if not config["quality"].get("allow_nulls", False):
        columns_to_check = [column for column in df.columns if column != "quality_errors"]

        null_mask = df[columns_to_check].isnull().any(axis=1)

        df.loc[null_mask, "quality_errors"] += "null_values;"

    if config["quality"].get("remove_duplicates", True):
        duplicate_mask = df.duplicated(
            subset=["datetime", "city", "country", "source"],
            keep="first"
        )

        df.loc[duplicate_mask, "quality_errors"] += "duplicate_record;"

    valid_ranges = config["quality"].get("valid_ranges", {})

    for column, rules in valid_ranges.items():
        if column not in df.columns:
            continue

        min_value = rules.get("min")
        max_value = rules.get("max")

        if min_value is not None:
            min_mask = df[column] < min_value
            df.loc[min_mask, "quality_errors"] += f"{column}_below_min;"

        if max_value is not None:
            max_mask = df[column] > max_value
            df.loc[max_mask, "quality_errors"] += f"{column}_above_max;"

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
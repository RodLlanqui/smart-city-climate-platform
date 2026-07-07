from typing import Any, Dict

import pandas as pd


def transform_hourly_weather(raw_data: Dict[str, Any], config: Dict[str, Any]) -> pd.DataFrame:
    """
    Transforma la respuesta horaria de Open-Meteo en un DataFrame tabular.

    Args:
        raw_data: Respuesta original de la API Open-Meteo.
        config: Configuración cargada desde YAML.

    Returns:
        DataFrame con datos meteorológicos horarios estructurados.
    """
    hourly_data = raw_data.get("hourly", {})

    if not hourly_data:
        raise ValueError("La respuesta no contiene datos horarios en la clave 'hourly'.")

    df = pd.DataFrame(hourly_data)

    if "time" not in df.columns:
        raise ValueError("La respuesta horaria no contiene la columna 'time'.")

    df = df.rename(columns={"time": "datetime"})

    df["datetime"] = pd.to_datetime(df["datetime"])

    df["city"] = config["location"]["city"]
    df["country"] = config["location"]["country"]
    df["latitude"] = raw_data.get("latitude")
    df["longitude"] = raw_data.get("longitude")
    df["timezone"] = raw_data.get("timezone")
    df["source"] = "open_meteo"

    ordered_columns = [
        "datetime",
        "city",
        "country",
        "latitude",
        "longitude",
        "timezone",
        "source",
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
        "surface_pressure",
    ]

    existing_columns = [column for column in ordered_columns if column in df.columns]

    return df[existing_columns]


def create_daily_weather_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea métricas meteorológicas diarias a partir de datos horarios válidos.

    Args:
        df: DataFrame con datos horarios validados.

    Returns:
        DataFrame con métricas agregadas por día, ciudad y fuente.
    """
    if df.empty:
        raise ValueError("No se pueden crear métricas Gold desde un DataFrame vacío.")

    required_columns = [
        "datetime",
        "city",
        "country",
        "latitude",
        "longitude",
        "timezone",
        "source",
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
        "surface_pressure",
    ]

    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        raise ValueError(f"Faltan columnas requeridas para Gold: {missing_columns}")

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
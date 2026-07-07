import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def build_bronze_filename(config: Dict[str, Any]) -> str:
    """
    Construye el nombre del archivo Bronze usando ciudad, fechas y timestamp de ingesta.

    Args:
        config: Diccionario de configuración cargado desde YAML.

    Returns:
        Nombre del archivo JSON para la capa Bronze.
    """
    city = config["location"]["city"].lower().replace(" ", "_")
    start_date = config["batch"]["start_date"]
    end_date = config["batch"]["end_date"]
    ingestion_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"open_meteo_{city}_{start_date}_{end_date}_{ingestion_timestamp}.json"


def save_json(data: Dict[str, Any], output_path: Path) -> Path:
    """
    Guarda un diccionario como archivo JSON.

    Args:
        data: Datos a guardar.
        output_path: Ruta completa del archivo de salida.

    Returns:
        Ruta del archivo guardado.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    return output_path


def save_bronze_data(data: Dict[str, Any], config: Dict[str, Any], bronze_dir: Path) -> Path:
    """
    Guarda la respuesta original de Open-Meteo en la capa Bronze.

    Args:
        data: Respuesta original de la API.
        config: Diccionario de configuración cargado desde YAML.
        bronze_dir: Directorio Bronze.

    Returns:
        Ruta del archivo guardado.
    """
    filename = build_bronze_filename(config)
    output_path = bronze_dir / filename

    return save_json(data, output_path)



def build_silver_filename(config: Dict[str, Any]) -> str:
    """
    Construye el nombre del archivo Silver usando ciudad y rango de fechas.

    Args:
        config: Diccionario de configuración cargado desde YAML.

    Returns:
        Nombre del archivo Parquet para la capa Silver.
    """
    city = config["location"]["city"].lower().replace(" ", "_")
    start_date = config["batch"]["start_date"]
    end_date = config["batch"]["end_date"]

    return f"weather_hourly_{city}_{start_date}_{end_date}.parquet"


def save_dataframe_as_parquet(df: pd.DataFrame, output_path: Path) -> Path:
    """
    Guarda un DataFrame como archivo Parquet.

    Args:
        df: DataFrame a guardar.
        output_path: Ruta completa del archivo de salida.

    Returns:
        Ruta del archivo guardado.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)

    return output_path


def save_silver_data(df: pd.DataFrame, config: Dict[str, Any], silver_dir: Path) -> Path:
    """
    Guarda los datos transformados en la capa Silver.

    Args:
        df: DataFrame transformado.
        config: Configuración cargada desde YAML.
        silver_dir: Directorio Silver.

    Returns:
        Ruta del archivo Parquet guardado.
    """
    filename = build_silver_filename(config)
    output_path = silver_dir / filename

    return save_dataframe_as_parquet(df, output_path)


def build_quarantine_filename(config: Dict[str, Any]) -> str:
    """
    Construye el nombre del archivo de cuarentena.

    Args:
        config: Diccionario de configuración cargado desde YAML.

    Returns:
        Nombre del archivo Parquet para la capa Quarantine.
    """
    city = config["location"]["city"].lower().replace(" ", "_")
    start_date = config["batch"]["start_date"]
    end_date = config["batch"]["end_date"]

    return f"weather_invalid_{city}_{start_date}_{end_date}.parquet"


def save_quarantine_data(df: pd.DataFrame, config: Dict[str, Any], quarantine_dir: Path) -> Path | None:
    """
    Guarda registros inválidos en la capa Quarantine.

    Args:
        df: DataFrame con registros inválidos.
        config: Configuración cargada desde YAML.
        quarantine_dir: Directorio Quarantine.

    Returns:
        Ruta del archivo guardado o None si no existen registros inválidos.
    """
    if df.empty:
        return None

    filename = build_quarantine_filename(config)
    output_path = quarantine_dir / filename

    return save_dataframe_as_parquet(df, output_path)


def build_gold_filename(config: Dict[str, Any]) -> str:
    """
    Construye el nombre del archivo Gold usando ciudad y rango de fechas.

    Args:
        config: Diccionario de configuración cargado desde YAML.

    Returns:
        Nombre del archivo Parquet para la capa Gold.
    """
    city = config["location"]["city"].lower().replace(" ", "_")
    start_date = config["batch"]["start_date"]
    end_date = config["batch"]["end_date"]

    return f"weather_daily_metrics_{city}_{start_date}_{end_date}.parquet"


def save_gold_data(df: pd.DataFrame, config: Dict[str, Any], gold_dir: Path) -> Path:
    """
    Guarda las métricas analíticas en la capa Gold.

    Args:
        df: DataFrame con métricas Gold.
        config: Configuración cargada desde YAML.
        gold_dir: Directorio Gold.

    Returns:
        Ruta del archivo Parquet guardado.
    """
    filename = build_gold_filename(config)
    output_path = gold_dir / filename

    return save_dataframe_as_parquet(df, output_path)
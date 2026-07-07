from pathlib import Path
from typing import Any, Dict

import requests
import sys


# Permite importar módulos desde src/common cuando ejecutamos este archivo directamente.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from common.config_loader import load_config


OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def build_archive_params(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construye los parámetros necesarios para consultar la API histórica de Open-Meteo.

    Args:
        config: Diccionario de configuración cargado desde YAML.

    Returns:
        Diccionario con los parámetros de consulta para la API.
    """
    location = config["location"]
    batch = config["batch"]

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "start_date": batch["start_date"],
        "end_date": batch["end_date"],
        "hourly": ",".join(batch["hourly_variables"]),
        "timezone": location["timezone"],
    }

    return params


def fetch_historical_weather(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Consulta datos históricos meteorológicos desde Open-Meteo.

    Args:
        config: Diccionario de configuración cargado desde YAML.

    Returns:
        Respuesta de la API en formato diccionario.

    Raises:
        requests.HTTPError: Si la API responde con error HTTP.
        requests.RequestException: Si ocurre un problema de conexión.
    """
    params = build_archive_params(config)

    response = requests.get(
        OPEN_METEO_ARCHIVE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    config = load_config()
    data = fetch_historical_weather(config)

    print("Datos históricos obtenidos correctamente desde Open-Meteo")
    print(f"Ciudad: {config['location']['city']}")
    print(f"País: {config['location']['country']}")
    print(f"Latitud consultada: {data.get('latitude')}")
    print(f"Longitud consultada: {data.get('longitude')}")
    print(f"Zona horaria: {data.get('timezone')}")
    print(f"Variables recibidas: {list(data.get('hourly', {}).keys())}")

    hourly_data = data.get("hourly", {})
    time_values = hourly_data.get("time", [])

    print(f"Cantidad de registros horarios: {len(time_values)}")

    if time_values:
        print(f"Primera fecha/hora: {time_values[0]}")
        print(f"Última fecha/hora: {time_values[-1]}")
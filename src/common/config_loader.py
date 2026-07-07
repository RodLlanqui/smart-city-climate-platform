from pathlib import Path
from typing import Any, Dict

import yaml


def load_config(config_path: str = "config/config.example.yaml") -> Dict[str, Any]:
    """
    Carga la configuración del proyecto desde un archivo YAML.

    Args:
        config_path: Ruta relativa o absoluta del archivo YAML.

    Returns:
        Diccionario con la configuración del proyecto.

    Raises:
        FileNotFoundError: Si el archivo de configuración no existe.
        ValueError: Si el archivo YAML está vacío o no se puede interpretar.
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {config_path}")

    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not config:
        raise ValueError("El archivo de configuración está vacío o no es válido.")

    return config


if __name__ == "__main__":
    config = load_config()

    print("Configuración cargada correctamente")
    print(f"Proyecto: {config['project']['name']}")
    print(f"Ambiente: {config['project']['environment']}")
    print(f"Ciudad: {config['location']['city']}")
    print(f"País: {config['location']['country']}")
    print(f"Fecha inicio Batch: {config['batch']['start_date']}")
    print(f"Fecha fin Batch: {config['batch']['end_date']}")
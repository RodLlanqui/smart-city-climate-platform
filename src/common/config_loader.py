from pathlib import Path
from typing import Any, Dict

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def resolve_config_path(config_path: str | Path | None = None) -> Path:
    """Resuelve una ruta de configuración desde la raíz del proyecto."""
    path = DEFAULT_CONFIG_PATH if config_path is None else Path(config_path)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path


def load_config(config_path: str | Path | None = None) -> Dict[str, Any]:
    """
    Carga la configuración del proyecto desde un archivo YAML.

    Args:
        config_path: Ruta relativa a la raíz del proyecto o absoluta. Si no se
            indica, se utiliza config/config.yaml.

    Returns:
        Diccionario con la configuración del proyecto.

    Raises:
        FileNotFoundError: Si el archivo de configuración no existe.
        ValueError: Si el archivo YAML está vacío o no se puede interpretar.
    """
    path = resolve_config_path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            "No se encontró la configuración local en "
            f"{path}. Crea config/config.yaml a partir de "
            "config/config.example.yaml."
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as error:
        raise ValueError(f"El archivo YAML no es válido: {path}") from error

    if not isinstance(config, dict) or not config:
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

from pathlib import Path
from typing import Dict


def get_project_root() -> Path:
    """
    Obtiene la ruta raíz del proyecto.

    Returns:
        Ruta absoluta de la carpeta principal del proyecto.
    """
    return Path(__file__).resolve().parents[2]


def resolve_path(relative_path: str) -> Path:
    """
    Convierte una ruta relativa del proyecto en una ruta absoluta.

    Args:
        relative_path: Ruta relativa definida desde la raíz del proyecto.

    Returns:
        Ruta absoluta.
    """
    return get_project_root() / relative_path


def ensure_directory(path: Path) -> None:
    """
    Crea una carpeta si no existe.

    Args:
        path: Ruta de la carpeta a crear.
    """
    path.mkdir(parents=True, exist_ok=True)


def ensure_storage_directories(storage_config: Dict[str, str]) -> None:
    """
    Crea las carpetas de almacenamiento definidas en la configuración.

    Args:
        storage_config: Sección 'storage' del archivo YAML.
    """
    for path_value in storage_config.values():
        directory = resolve_path(path_value)
        ensure_directory(directory)


if __name__ == "__main__":
    from config_loader import load_config

    config = load_config()
    ensure_storage_directories(config["storage"])

    print("Carpetas de almacenamiento verificadas correctamente:")
    for name, path_value in config["storage"].items():
        print(f"{name}: {resolve_path(path_value)}")
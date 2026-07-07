from pathlib import Path
import sys


# Permite importar módulos internos desde la carpeta src.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from common.config_loader import load_config
from common.paths import ensure_storage_directories, resolve_path
from batch.extract import fetch_historical_weather
from batch.load import (
    save_bronze_data,
    save_gold_data,
    save_quarantine_data,
    save_silver_data,
)
from batch.quality import build_quality_summary, split_valid_invalid_records
from batch.transform import create_daily_weather_metrics, transform_hourly_weather


def run_batch_pipeline() -> None:
    """
    Ejecuta la versión del pipeline Batch local hasta la capa Gold.

    Flujo actual:
    1. Carga configuración.
    2. Verifica carpetas de almacenamiento.
    3. Extrae datos históricos desde Open-Meteo.
    4. Guarda la respuesta original en Bronze.
    5. Transforma datos horarios a formato tabular.
    6. Valida calidad de datos.
    7. Guarda registros válidos en Silver.
    8. Guarda registros inválidos en Quarantine, si existen.
    9. Crea métricas diarias.
    10. Guarda métricas analíticas en Gold.
    """
    print("Iniciando pipeline Batch local...")

    config = load_config()
    ensure_storage_directories(config["storage"])

    print("Configuración cargada correctamente.")
    print(f"Ciudad: {config['location']['city']}")
    print(f"Rango de fechas: {config['batch']['start_date']} a {config['batch']['end_date']}")

    print("Consultando datos históricos desde Open-Meteo...")
    raw_data = fetch_historical_weather(config)

    bronze_dir = resolve_path(config["storage"]["bronze_path"])
    silver_dir = resolve_path(config["storage"]["silver_path"])
    gold_dir = resolve_path(config["storage"]["gold_path"])
    quarantine_dir = resolve_path(config["storage"]["quarantine_path"])

    print("Guardando respuesta original en Bronze...")
    bronze_file_path = save_bronze_data(raw_data, config, bronze_dir)

    print("Transformando datos hacia formato tabular...")
    transformed_df = transform_hourly_weather(raw_data, config)

    print(f"Registros transformados: {len(transformed_df)}")
    print(f"Columnas generadas: {list(transformed_df.columns)}")

    print("Aplicando reglas de calidad...")
    valid_df, invalid_df = split_valid_invalid_records(transformed_df, config)

    quality_summary = build_quality_summary(transformed_df, valid_df, invalid_df)

    print("Resumen de calidad:")
    print(f"Total de registros: {quality_summary['total_records']}")
    print(f"Registros válidos: {quality_summary['valid_records']}")
    print(f"Registros inválidos: {quality_summary['invalid_records']}")

    print("Guardando registros válidos en Silver...")
    silver_file_path = save_silver_data(valid_df, config, silver_dir)

    quarantine_file_path = save_quarantine_data(invalid_df, config, quarantine_dir)

    if quarantine_file_path:
        print(f"Registros inválidos guardados en Quarantine: {quarantine_file_path}")
    else:
        print("No se detectaron registros inválidos. No se generó archivo de cuarentena.")

    print("Generando métricas diarias para Gold...")
    gold_df = create_daily_weather_metrics(valid_df)

    print(f"Registros Gold generados: {len(gold_df)}")
    print(f"Columnas Gold: {list(gold_df.columns)}")

    print("Guardando métricas en Gold...")
    gold_file_path = save_gold_data(gold_df, config, gold_dir)

    print("Pipeline Batch ejecutado correctamente.")
    print(f"Archivo Bronze generado: {bronze_file_path}")
    print(f"Archivo Silver generado: {silver_file_path}")
    print(f"Archivo Gold generado: {gold_file_path}")


if __name__ == "__main__":
    run_batch_pipeline()
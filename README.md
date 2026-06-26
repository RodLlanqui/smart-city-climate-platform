# Smart City Climate Platform

Plataforma de ingeniería de datos para recopilar, procesar, validar, almacenar y visualizar información meteorológica histórica y actual.

## Estado del proyecto

En desarrollo.

Actualmente se está trabajando en la preparación del repositorio y en la construcción del pipeline Batch local.

## Objetivo

Diseñar e implementar una plataforma de datos climáticos utilizando procesos Batch y Streaming, una arquitectura por capas Bronze, Silver y Gold, y servicios de Google Cloud.

## Tecnologías previstas

- Python
- pandas
- Open-Meteo API
- Apache Parquet
- Google Cloud Storage
- Pub/Sub
- BigQuery
- Cloud Run
- Cloud Scheduler
- PySpark
- Apache Airflow
- Looker Studio

## Arquitectura

El proyecto se organizará en las siguientes capas:

- **Bronze:** datos originales obtenidos desde la fuente.
- **Silver:** datos limpios, estandarizados y validados.
- **Gold:** métricas y datos preparados para análisis.
- **Quarantine:** registros que no cumplen las reglas de calidad.

## Estructura del proyecto

```text
smart-city-climate-platform/
├── config/
├── src/
│   ├── batch/
│   ├── streaming/
│   └── common/
├── data/
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── quarantine/
├── sql/
├── tests/
├── infrastructure/
├── dashboard/
└── docs/
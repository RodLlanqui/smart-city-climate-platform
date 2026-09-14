import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "surface_pressure",
]


@pytest.fixture
def batch_config():
    return {
        "project": {
            "name": "smart-city-climate-platform",
            "environment": "test",
        },
        "open_meteo": {
            "archive_url": "https://example.test/open-meteo/archive",
        },
        "location": {
            "city": "Santiago",
            "country": "Chile",
            "latitude": -33.4489,
            "longitude": -70.6693,
            "timezone": "America/Santiago",
        },
        "batch": {
            "start_date": "2025-01-01",
            "end_date": "2025-01-01",
            "hourly_variables": HOURLY_VARIABLES.copy(),
        },
        "storage": {
            "bronze_path": "data/bronze",
            "silver_path": "data/silver",
            "gold_path": "data/gold",
            "quarantine_path": "data/quarantine",
        },
        "quality": {
            "allow_nulls": False,
            "remove_duplicates": True,
            "valid_ranges": {
                "temperature_2m": {"min": -50, "max": 60},
                "relative_humidity_2m": {"min": 0, "max": 100},
                "precipitation": {"min": 0},
                "wind_speed_10m": {"min": 0},
                "surface_pressure": {"min": 800, "max": 1100},
            },
        },
    }


@pytest.fixture
def open_meteo_response():
    return {
        "latitude": -33.4489,
        "longitude": -70.6693,
        "timezone": "America/Santiago",
        "hourly": {
            "time": [
                "2025-01-01T00:00",
                "2025-01-01T01:00",
                "2025-01-01T02:00",
            ],
            "temperature_2m": [20.0, 22.0, 21.0],
            "relative_humidity_2m": [50, 60, 55],
            "precipitation": [0.2, 0.0, 0.3],
            "wind_speed_10m": [4.0, 8.0, 5.0],
            "surface_pressure": [950.0, 951.0, 949.0],
        },
    }


@pytest.fixture
def transformed_dataframe(open_meteo_response, batch_config):
    from batch.transform import transform_hourly_weather

    return transform_hourly_weather(open_meteo_response, batch_config)

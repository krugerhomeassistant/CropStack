"""Run CropStack with outside services stubbed, for browser tests and screenshots (no network, no quota).

    cd backend && CROPSTACK_DATA_DIR=/tmp/cs-e2e CROPSTACK_STATIC_DIR=../frontend/dist \\
        CROPSTACK_SCHEDULER=false python -m tests.e2e_server --port 8512

Climate: a synthetic winter-rainfall climate with a warming trend. Forecast: 92 past + 16 future days.
"""

import argparse
from datetime import UTC, date, datetime, timedelta

import uvicorn

from app import external
from app.main import app
from tests.test_climate import synthetic

WEATHER_CODES = [0, 1, 3, 61, 80, 2, 0, 95, 3, 1]


def fake_forecast(lat: float, lon: float) -> dict:
    today = datetime.now(UTC).date()
    n = 108
    days = [today - timedelta(days=92 - i) for i in range(n)]
    return {
        "timezone": "UTC",
        "utc_offset_seconds": 0,
        "daily": {
            "time": [d.isoformat() for d in days],
            "temperature_2m_min": [11 + (i % 5) for i in range(n)],
            "temperature_2m_max": [22 + (i % 7) for i in range(n)],
            "precipitation_sum": [3.2 if i % 4 == 0 else 0 for i in range(n)],
            "precipitation_probability_max": [(i * 13) % 90 for i in range(n)],
            "et0_fao_evapotranspiration": [4.0] * n,
            "relative_humidity_2m_mean": [60.0] * n,
            "wind_speed_10m_max": [18.0] * n,
            "soil_temperature_0_to_7cm_mean": [17.0] * n,
            "weather_code": [WEATHER_CODES[i % len(WEATHER_CODES)] for i in range(n)],
        },
    }


def fake_archive(lat: float, lon: float, today: date | None = None) -> dict:
    return synthetic(
        mean=11, amplitude=5, coldest=date(2001, 7, 15), day_range=15, rain_cold=2.5, rain_warm=0.3, year_shift=1.5
    )


def fake_places(query: str, limit: int = 5) -> list[dict]:
    return [
        {"label": f"{query}, Western Cape, South Africa", "latitude": -33.93, "longitude": 18.86, "postal_code": "7600"}
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8512)
    args = parser.parse_args()
    external.fetch_climate_archive = fake_archive
    external.fetch_forecast = fake_forecast
    external.search_places = fake_places
    uvicorn.run(app, host="127.0.0.1", port=args.port)

"""Weather provider for the daily style assistant (PRD §12: weather-aware).

Uses Open-Meteo (free, keyless) with a 30-minute per-city cache. Any failure —
no network, unknown city, rate limit — falls back to a deterministic seasonal
profile so the feature never breaks (zero-dependency dev parity).
"""
import calendar
import logging
from dataclasses import dataclass

import httpx
from django.core.cache import cache

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_TTL_SECONDS = 1800
REQUEST_TIMEOUT_SECONDS = 4.0

# India-centric seasonal defaults (month -> temp band + condition)
SEASONAL_BANDS = {
    12: (24.0, "Pleasant & clear"), 1: (23.0, "Pleasant & clear"), 2: (26.0, "Warm days, cool evenings"),
    3: (32.0, "Hot & sunny"), 4: (35.0, "Very hot & dry"), 5: (36.0, "Very hot & dry"),
    6: (31.0, "Humid, rain likely"), 7: (28.0, "Monsoon showers"), 8: (28.0, "Monsoon showers"),
    9: (29.0, "Humid, easing rain"),
    10: (30.0, "Warm & clearing"), 11: (27.0, "Warm & breezy"),
}

RAIN_CODES = set(range(51, 68)) | set(range(80, 83)) | {95, 96, 99}


@dataclass(frozen=True)
class WeatherSnapshot:
    city: str
    temp_c: float
    condition: str
    is_rainy: bool
    source: str  # "open-meteo" | "seasonal-default"

    @property
    def is_mock(self) -> bool:
        return self.source == "seasonal-default"


def _fallback(city: str) -> WeatherSnapshot:
    from django.utils import timezone

    month = timezone.localdate().month
    temp_c, condition = SEASONAL_BANDS.get(month, (29.0, "Warm & breezy"))
    return WeatherSnapshot(city=city or "your area", temp_c=temp_c,
                           condition=condition, is_rainy=condition.startswith("Monsoon"),
                           source="seasonal-default")


def _describe(code: int) -> str:
    if code in RAIN_CODES:
        return "Rain likely"
    if code in (0, 1):
        return "Clear skies"
    if code in (2, 3):
        return "Cloudy"
    if code in (45, 48):
        return "Foggy"
    return "Changeable skies"


def get_weather(city: str | None) -> WeatherSnapshot | None:
    """Best-effort current weather for a city; None only if no city given at all."""
    if not city or not city.strip():
        return None
    city = city.strip()[:80]
    cache_key = f"wx:{city.lower().replace(' ', '-')}"
    cached = cache.get(cache_key)
    if isinstance(cached, WeatherSnapshot):
        return cached

    snapshot = _fetch_live(city) or _fallback(city)
    cache.set(cache_key, snapshot, CACHE_TTL_SECONDS)
    return snapshot


def _fetch_live(city: str) -> WeatherSnapshot | None:
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            geo = client.get(GEOCODING_URL, params={"name": city, "count": 1, "language": "en"})
            geo.raise_for_status()
            results = geo.json().get("results") or []
            if not results:
                return None
            place = results[0]

            forecast = client.get(FORECAST_URL, params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,weather_code",
            })
            forecast.raise_for_status()
            current = forecast.json().get("current") or {}
            temp_c = current.get("temperature_2m")
            if temp_c is None:
                return None
            code = int(current.get("weather_code") or 0)
            return WeatherSnapshot(
                city=place.get("name", city),
                temp_c=float(temp_c),
                condition=_describe(code),
                is_rainy=code in RAIN_CODES,
                source="open-meteo",
            )
    except Exception as exc:  # noqa: BLE001 - weather must never break styling
        logger.info("Weather lookup failed for %s (%s); using seasonal default", city, exc)
        return None


def month_name(month_index: int) -> str:
    return calendar.month_name[month_index]

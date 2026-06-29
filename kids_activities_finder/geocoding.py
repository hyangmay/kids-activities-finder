"""Turn a coarse location string into an approximate center point.

We accept only coarse input — ZIP, neighborhood, or street/cross-streets — never a house
number (see CLAUDE.md privacy notes). A single center point plus a search radius is all
the downstream distance filtering needs.

Geocoding uses OpenStreetMap's free Nominatim service. Two things matter for correctness
and politeness:

* **US bias.** A bare ZIP like ``97214`` matches postcodes worldwide (it resolves to
  Crimea without biasing!). We constrain results to the US so coarse input lands where
  the user expects. This is adjustable as more regions come online.
* **Rate limits.** Nominatim's usage policy allows at most ~1 request/second and requires
  a descriptive User-Agent. We serialize requests and identify ourselves.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import requests

from .cache import TTLCache

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Identify the app per Nominatim's usage policy (a contact/app name is required).
USER_AGENT = "kids-activities-finder/0.1 (https://github.com/; toddler activity finder)"

# Nominatim asks for no more than 1 request per second.
_MIN_INTERVAL_SECONDS = 1.0

# Coarse input rarely changes within a session; cache results for an hour.
_GEOCODE_TTL_SECONDS = 60 * 60

# Default country bias. The architecture is location-agnostic, but the only region with
# real data today is the US (Portland, OR), and US biasing is what makes coarse ZIP input
# resolve correctly. Revisit when non-US regions are added.
DEFAULT_COUNTRY_CODES = "us"


@dataclass(frozen=True)
class GeocodeResult:
    """An approximate center point for the user's chosen area."""

    lat: float
    lon: float
    display_name: str  # human-readable, e.g. "97214, Buckman, Portland, ..."
    query: str  # the original input, for display/debugging


class GeocodingError(RuntimeError):
    """Raised when a location string can't be resolved."""


_cache: TTLCache[tuple[str, str], GeocodeResult] = TTLCache(_GEOCODE_TTL_SECONDS)
_rate_lock = threading.Lock()
_last_request_at = 0.0


def _throttle() -> None:
    """Block until at least ``_MIN_INTERVAL_SECONDS`` since the last request."""
    global _last_request_at
    with _rate_lock:
        wait = _MIN_INTERVAL_SECONDS - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
        _last_request_at = time.monotonic()


def geocode(
    query: str,
    *,
    country_codes: str = DEFAULT_COUNTRY_CODES,
    session: requests.Session | None = None,
    timeout: float = 10.0,
) -> GeocodeResult:
    """Resolve a coarse location string to a :class:`GeocodeResult`.

    Raises :class:`GeocodingError` for empty input or when nothing is found.
    """
    cleaned = query.strip()
    if not cleaned:
        raise GeocodingError("Please enter a ZIP code, neighborhood, or street.")

    cache_key = (cleaned.lower(), country_codes)
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    _throttle()
    http = session or requests
    params = {
        "q": cleaned,
        "format": "json",
        "limit": 1,
        "addressdetails": 0,
    }
    if country_codes:
        params["countrycodes"] = country_codes

    try:
        resp = http.get(
            NOMINATIM_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        resp.raise_for_status()
        results = resp.json()
    except requests.RequestException as exc:
        raise GeocodingError(f"Couldn't reach the geocoding service: {exc}") from exc
    except ValueError as exc:  # bad JSON
        raise GeocodingError("Got an unexpected response from the geocoding service.") from exc

    if not results:
        raise GeocodingError(
            f"Couldn't find “{cleaned}”. Try a ZIP code, neighborhood, or nearby street."
        )

    top = results[0]
    result = GeocodeResult(
        lat=float(top["lat"]),
        lon=float(top["lon"]),
        display_name=top.get("display_name", cleaned),
        query=cleaned,
    )
    _cache.set(cache_key, result)
    return result

"""Geocoding tests use a fake HTTP session — no real network calls."""

import pytest

from kids_activities_finder import geocoding
from kids_activities_finder.geocoding import GeocodingError, geocode


class _FakeResponse:
    def __init__(self, json_data, status=200):
        self._json = json_data
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise geocoding.requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._json


class _FakeSession:
    def __init__(self, json_data):
        self._json = json_data
        self.last_params = None

    def get(self, url, params=None, headers=None, timeout=None):
        self.last_params = params
        return _FakeResponse(self._json)


@pytest.fixture(autouse=True)
def _clear_geocode_cache():
    geocoding._cache.clear()
    yield
    geocoding._cache.clear()


def test_empty_query_raises():
    with pytest.raises(GeocodingError):
        geocode("   ")


def test_successful_geocode_sets_us_bias():
    session = _FakeSession(
        [{"lat": "45.5142", "lon": "-122.6389", "display_name": "97214, Portland, OR"}]
    )
    result = geocode("97214", session=session)
    assert result.lat == pytest.approx(45.5142)
    assert result.lon == pytest.approx(-122.6389)
    assert "Portland" in result.display_name
    assert session.last_params["countrycodes"] == "us"


def test_no_results_raises():
    with pytest.raises(GeocodingError):
        geocode("asdkjfhqweoiu", session=_FakeSession([]))


def test_result_is_cached():
    session = _FakeSession(
        [{"lat": "45.0", "lon": "-122.0", "display_name": "somewhere"}]
    )
    first = geocode("Sellwood", session=session)
    # A second call with a session that would return nothing still returns the cached hit.
    second = geocode("Sellwood", session=_FakeSession([]))
    assert (second.lat, second.lon) == (first.lat, first.lon)

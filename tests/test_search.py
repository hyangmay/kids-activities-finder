"""Search-engine tests with fake geocoding and fake sources — no network."""

from datetime import date, datetime, timedelta

import pytest

from kids_activities_finder import search as search_mod
from kids_activities_finder.geocoding import GeocodeResult
from kids_activities_finder.models import Activity
from kids_activities_finder.search import search
from kids_activities_finder.sources.base import Source
from kids_activities_finder.timewindow import ALL_DAYS, Day

TODAY = date(2026, 6, 28)
# A center point in inner SE Portland.
CENTER = GeocodeResult(lat=45.5142, lon=-122.6389, display_name="97214, Portland", query="97214")


class _StaticSource(Source):
    name = "Static"
    region = "Portland, OR"

    def __init__(self, activities):
        self._activities = activities

    def fetch(self, window):
        return list(self._activities)


class _BrokenSource(Source):
    name = "Broken"
    region = "Portland, OR"

    def fetch(self, window):
        raise RuntimeError("upstream is down")


def _activity(title, day_offset, hour, lat, lon, **kw):
    start = datetime(TODAY.year, TODAY.month, TODAY.day, hour) + timedelta(days=day_offset)
    return Activity(title=title, source="Static", start=start, lat=lat, lon=lon, **kw)


@pytest.fixture(autouse=True)
def _patch_geocode_and_clear_cache(monkeypatch):
    monkeypatch.setattr(search_mod, "geocode", lambda q: CENTER)
    search_mod._fetch_cache.clear()
    yield
    search_mod._fetch_cache.clear()


def _patch_sources(monkeypatch, sources):
    monkeypatch.setattr(search_mod, "get_sources", lambda region=None: list(sources))


def test_filters_by_radius(monkeypatch):
    near = _activity("Near", 0, 10, 45.5152, -122.6390)  # ~0.1 mi
    far = _activity("Far", 0, 11, 45.9, -122.6)  # ~27 mi away
    _patch_sources(monkeypatch, [_StaticSource([near, far])])

    result = search("97214", list(ALL_DAYS), radius_miles=10, today=TODAY)
    titles = [a.title for a in result.activities]
    assert "Near" in titles
    assert "Far" not in titles


def test_filters_by_day(monkeypatch):
    today_act = _activity("Today", 0, 10, 45.5152, -122.6390)
    out_of_window = _activity("WayLater", 5, 10, 45.5152, -122.6390)
    _patch_sources(monkeypatch, [_StaticSource([today_act, out_of_window])])

    result = search("97214", [Day.TODAY], radius_miles=10, today=TODAY)
    assert [a.title for a in result.activities] == ["Today"]


def test_graceful_degradation_records_error_but_returns_rest(monkeypatch):
    good = _activity("Good", 0, 10, 45.5152, -122.6390)
    _patch_sources(monkeypatch, [_BrokenSource(), _StaticSource([good])])

    result = search("97214", list(ALL_DAYS), radius_miles=10, today=TODAY)
    assert [a.title for a in result.activities] == ["Good"]
    assert result.ok is False
    assert result.errors[0].source == "Broken"


def test_sorted_by_start_then_distance(monkeypatch):
    later = _activity("Later", 0, 14, 45.5152, -122.6390)
    earlier_far = _activity("EarlierFar", 0, 9, 45.5300, -122.6100)
    earlier_near = _activity("EarlierNear", 0, 9, 45.5145, -122.6389)
    _patch_sources(monkeypatch, [_StaticSource([later, earlier_far, earlier_near])])

    result = search("97214", list(ALL_DAYS), radius_miles=15, today=TODAY)
    assert [a.title for a in result.activities] == ["EarlierNear", "EarlierFar", "Later"]


def test_distance_is_populated(monkeypatch):
    near = _activity("Near", 0, 10, 45.5152, -122.6390)
    _patch_sources(monkeypatch, [_StaticSource([near])])

    result = search("97214", list(ALL_DAYS), radius_miles=10, today=TODAY)
    assert result.activities[0].distance_miles is not None
    assert result.activities[0].distance_miles < 1


def test_empty_days_raises(monkeypatch):
    _patch_sources(monkeypatch, [_StaticSource([])])
    with pytest.raises(ValueError):
        search("97214", [], today=TODAY)

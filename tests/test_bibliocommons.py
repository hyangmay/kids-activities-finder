"""BiblioCommons adapter tests — crafted API payloads, no network."""

from datetime import datetime

import pytest

from kids_activities_finder.sources.bibliocommons import BiblioCommonsSource
from kids_activities_finder.timewindow import ALL_DAYS, SearchWindow

WINDOW = SearchWindow.from_days(list(ALL_DAYS))

_LOCATIONS = {
    "9": {
        "id": "9",
        "name": "Beaverton City Library",
        "address": {
            "number": "12375",
            "street": "SW Fifth St",
            "city": "Beaverton",
            "state": "OR",
            "zip": "97005",
        },
        "mapLocation": {"centrePoint": {"lat": 45.484, "lng": -122.804}},
    },
    "99": {"id": "99", "name": "Mystery Branch", "address": None, "mapLocation": None},
}
_AUDIENCES = {
    "kid": {"id": "kid", "name": "Babies / Toddlers / Preschool"},
    "adult": {"id": "adult", "name": "Adults"},
}


def _event(eid, title, *, key, branch="9", audiences=("kid",), cancelled=False, desc=""):
    return {
        "id": eid,
        "key": key,
        "definition": {
            "title": title,
            "description": desc,
            "branchLocationId": branch,
            "audienceIds": list(audiences),
            "isCancelled": cancelled,
        },
    }


def _payload(events, *, page=1, pages=1):
    return {
        "events": {
            "items": [e["id"] for e in events],
            "pagination": {"page": page, "pages": pages, "count": len(events), "limit": 250},
        },
        "entities": {
            "events": {e["id"]: e for e in events},
            "locations": _LOCATIONS,
            "eventAudiences": _AUDIENCES,
        },
    }


class _FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


class _FakeSession:
    """Returns a payload per page number so we can exercise pagination."""

    def __init__(self, pages: dict[int, dict]):
        self._pages = pages
        self.calls = 0

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls += 1
        return _FakeResponse(self._pages[params["page"]])


def _source(session, **kw):
    return BiblioCommonsSource(
        slug="wccls",
        name="WCCLS",
        region="Portland, OR",
        event_base_url="https://wccls.bibliocommons.com/events",
        session=session,
        **kw,
    )


def test_maps_fields_and_filters():
    events = [
        _event("e1", "Toddler Storytime", key="2026-06-30T10:30:00",
               desc="<p>Songs &amp; <b>rhymes</b></p>"),
        _event("e2", "Adult Book Club", key="2026-06-30T18:00:00", audiences=("adult",)),
        _event("e3", "Cancelled Kids Thing", key="2026-06-30T10:00:00", cancelled=True),
        _event("e4", "Storytime (no coords)", key="2026-06-30T11:00:00", branch="99"),
    ]
    src = _source(_FakeSession({1: _payload(events)}))
    acts = src.fetch(WINDOW)

    # e2 (adults) and e3 (cancelled) are excluded; e1 and e4 remain.
    titles = [a.title for a in acts]
    assert titles == ["Toddler Storytime", "Storytime (no coords)"]

    e1 = acts[0]
    assert e1.source == "WCCLS"
    assert e1.start == datetime(2026, 6, 30, 10, 30)
    assert e1.url == "https://wccls.bibliocommons.com/events/e1"
    assert e1.is_free is True
    assert "Babies / Toddlers / Preschool" in e1.age_suitability
    assert e1.location_name == "Beaverton City Library"
    assert e1.address == "12375 SW Fifth St, Beaverton, OR 97005"
    assert (round(e1.lat, 3), round(e1.lon, 3)) == (45.484, -122.804)
    assert e1.description == "Songs & rhymes"  # HTML stripped, entities decoded

    # Branch without coordinates still yields an activity, just unplaceable.
    assert acts[1].has_coordinates is False


def test_kids_only_false_keeps_adult_events():
    events = [
        _event("e1", "Toddler Storytime", key="2026-06-30T10:30:00"),
        _event("e2", "Adult Book Club", key="2026-06-30T18:00:00", audiences=("adult",)),
    ]
    src = _source(_FakeSession({1: _payload(events)}), kids_only=False)
    assert len(src.fetch(WINDOW)) == 2


def test_pagination_merges_all_pages():
    p1 = _payload([_event("e1", "Day 1", key="2026-06-30T10:00:00")], page=1, pages=2)
    p2 = _payload([_event("e2", "Day 2", key="2026-07-01T10:00:00")], page=2, pages=2)
    session = _FakeSession({1: p1, 2: p2})
    acts = _source(session).fetch(WINDOW)
    assert session.calls == 2
    assert {a.title for a in acts} == {"Day 1", "Day 2"}

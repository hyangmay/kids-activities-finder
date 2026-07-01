"""BiblioCommons events adapter.

BiblioCommons powers the events calendars of many US library systems, and exposes a
clean public JSON gateway (no API key) at::

    https://gateway.bibliocommons.com/v2/libraries/<slug>/events

Because it's one well-structured API, a single adapter — parameterized by library slug —
covers every BiblioCommons library. The first one we wire up is **WCCLS** (Washington
County Cooperative Library Services), which in one feed covers Beaverton, Tigard,
Tualatin, Hillsboro, and ~a dozen more branches in the Portland metro.

The API is a normalizer's dream: each event carries a start time, a branch id that maps to
a branch with real coordinates, and audience tags — so we can place events on a map, sort
by time, and keep just the kid-friendly ones without any geocoding or HTML scraping.
"""

from __future__ import annotations

from datetime import datetime

import requests
from bs4 import BeautifulSoup

from ..models import Activity
from ..timewindow import SearchWindow
from .base import Source

GATEWAY_URL = "https://gateway.bibliocommons.com/v2/libraries/{slug}/events"

# Audience labels (as the API names them) that make an event relevant to this app.
KID_AUDIENCES = {"Babies / Toddlers / Preschool", "Kids"}

# The gateway rejects very large page sizes; 250 is the most it reliably returns.
_PAGE_SIZE = 250
# Safety bound so a huge system can't make us page forever.
_MAX_PAGES = 15

_HEADERS = {
    "User-Agent": (
        "kids-activities-finder/0.1 (toddler activity finder; contact via project repo)"
    ),
    "Accept": "application/json",
}


class BiblioCommonsSource(Source):
    """Events from any BiblioCommons library, via the public gateway API."""

    def __init__(
        self,
        *,
        slug: str,
        name: str,
        region: str,
        event_base_url: str,
        kids_only: bool = True,
        session: requests.Session | None = None,
        timeout: float = 15.0,
    ) -> None:
        """
        ``slug`` is the library id in the gateway URL (e.g. ``"wccls"``).
        ``event_base_url`` is where a human-facing event lives, so we can link to it
        (e.g. ``"https://wccls.bibliocommons.com/events"`` → ``.../events/<id>``).
        ``kids_only`` keeps only events tagged for babies/toddlers/preschool or kids.
        """
        self.name = name
        self.region = region
        self.slug = slug
        self.event_base_url = event_base_url.rstrip("/")
        self.kids_only = kids_only
        self._session = session or requests
        self._timeout = timeout

    def fetch(self, window: SearchWindow) -> list[Activity]:
        raw_events, entities = self._fetch_all(window)
        activities: list[Activity] = []
        for ev in raw_events:
            activity = self._to_activity(ev, entities)
            if activity is not None:
                activities.append(activity)
        return activities

    # --- network ---

    def _fetch_all(self, window: SearchWindow) -> tuple[list[dict], "_Entities"]:
        """Page through the window and return (events, merged-entities)."""
        url = GATEWAY_URL.format(slug=self.slug)
        base_params = {
            "startDate": window.start.isoformat(),
            "endDate": window.end.isoformat(),
            "limit": _PAGE_SIZE,
        }

        events: list[dict] = []
        entities = _Entities()
        page = 1
        while page <= _MAX_PAGES:
            resp = self._session.get(
                url, params={**base_params, "page": page}, headers=_HEADERS, timeout=self._timeout
            )
            resp.raise_for_status()
            payload = resp.json()
            block = payload.get("events", {})
            page_entities = payload.get("entities", {})
            entities.merge(page_entities)

            # The event objects live in entities.events, keyed by id; items gives order.
            item_ids = block.get("items", [])
            events.extend(entities.events[i] for i in item_ids if i in entities.events)

            pagination = block.get("pagination", {})
            if page >= pagination.get("pages", page):
                break
            page += 1

        return events, entities

    # --- mapping ---

    def _to_activity(self, ev: dict, entities: "_Entities") -> Activity | None:
        definition = ev.get("definition", {})
        if definition.get("isCancelled"):
            return None

        audiences = [
            entities.audience_name(a) for a in definition.get("audienceIds", [])
        ]
        audiences = [a for a in audiences if a]
        if self.kids_only and not (set(audiences) & KID_AUDIENCES):
            return None

        start = _parse_local(ev.get("key"))
        branch = entities.locations.get(definition.get("branchLocationId"), {})
        lat, lon = _branch_coords(branch)

        return Activity(
            title=definition.get("title", "Untitled event"),
            source=self.name,
            start=start,
            end=None,  # occurrence end isn't reliably distinct from the day boundary
            description=_clean_html(definition.get("description", "")),
            url=f"{self.event_base_url}/{ev.get('id')}" if ev.get("id") else "",
            is_free=True,  # public library programs are free
            age_suitability=", ".join(audiences),
            location_name=branch.get("name", ""),
            address=_format_address(branch.get("address")),
            lat=lat,
            lon=lon,
        )


class _Entities:
    """Accumulates the shared entity dictionaries returned alongside each page."""

    def __init__(self) -> None:
        self.events: dict[str, dict] = {}
        self.locations: dict[str, dict] = {}
        self.audiences: dict[str, dict] = {}

    def merge(self, block: dict) -> None:
        self.events.update(block.get("events", {}))
        self.locations.update(block.get("locations", {}))
        self.audiences.update(block.get("eventAudiences", {}))

    def audience_name(self, audience_id: str) -> str:
        return self.audiences.get(audience_id, {}).get("name", "")


def _parse_local(key: str | None) -> datetime | None:
    """The ``key`` field is the occurrence start as a naive local datetime string."""
    if not key:
        return None
    try:
        return datetime.fromisoformat(key)
    except ValueError:
        return None


def _branch_coords(branch: dict) -> tuple[float | None, float | None]:
    centre = (branch.get("mapLocation") or {}).get("centrePoint") or {}
    lat, lng = centre.get("lat"), centre.get("lng")
    if lat is None or lng is None:
        return None, None
    return float(lat), float(lng)


def _format_address(address: dict | None) -> str:
    if not address:
        return ""
    number = (address.get("number") or "").strip()
    street = (address.get("street") or "").strip()
    line1 = " ".join(p for p in (number, street) if p)
    city = address.get("city", "")
    state = address.get("state", "")
    zip_code = address.get("zip", "")
    tail = f"{city}, {state} {zip_code}".strip().strip(",")
    return ", ".join(p for p in (line1, tail) if p)


def _clean_html(html: str) -> str:
    if not html:
        return ""
    text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    return " ".join(text.split())

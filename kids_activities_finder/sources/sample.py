"""A sample Portland source with hand-written placeholder data.

Why this exists: every real Portland source we surveyed (library, parks, OMSI, zoo) is a
JavaScript-rendered app with no stable public feed, so each real adapter needs its own
reverse-engineering. This source lets the *rest* of the app — geocoding, distance,
windowing, sorting, the UI — work end-to-end and be tested today, before any scraper is
written.

It is clearly labeled as sample data (titles are suffixed and ``source`` says so) and is
designed to be deleted once real sources exist. It generates a handful of plausible
toddler activities at real Portland venues, on whatever days the user searched.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from ..models import Activity
from ..timewindow import SearchWindow
from .base import Source

REGION = "Portland, OR"


@dataclass(frozen=True)
class _Venue:
    name: str
    address: str
    lat: float
    lon: float


@dataclass(frozen=True)
class _Template:
    """A recurring-ish activity to instantiate on each searched day."""

    title: str
    venue: _Venue
    at: time
    duration_minutes: int
    is_free: bool
    age_suitability: str
    description: str
    url: str
    # Only emit on these weekdays (Mon=0 … Sun=6); empty means any day.
    weekdays: tuple[int, ...] = ()


# Real Portland venues with approximate coordinates, so distance filtering is meaningful.
_SELLWOOD_LIBRARY = _Venue(
    "Sellwood Moreland Library",
    "7860 SE 13th Ave, Portland, OR 97202",
    45.4636,
    -122.6536,
)
_BELMONT_LIBRARY = _Venue(
    "Belmont Library",
    "1038 SE César E. Chávez Blvd, Portland, OR 97214",
    45.5165,
    -122.6235,
)
_OMSI = _Venue(
    "OMSI",
    "1945 SE Water Ave, Portland, OR 97214",
    45.5083,
    -122.6656,
)
_OREGON_ZOO = _Venue(
    "Oregon Zoo",
    "4001 SW Canyon Rd, Portland, OR 97221",
    45.5099,
    -122.7157,
)
_GRANT_PARK = _Venue(
    "Grant Park Playground",
    "NE 33rd Ave & US Grant Pl, Portland, OR 97212",
    45.5409,
    -122.6285,
)


_TEMPLATES: tuple[_Template, ...] = (
    _Template(
        title="Toddler Story Time",
        venue=_SELLWOOD_LIBRARY,
        at=time(10, 30),
        duration_minutes=30,
        is_free=True,
        age_suitability="Ages 0–3",
        description="Songs, rhymes, and picture books for little ones and their grown-ups.",
        url="https://multcolib.org/events",
    ),
    _Template(
        title="Baby & Me Lapsit",
        venue=_BELMONT_LIBRARY,
        at=time(11, 15),
        duration_minutes=30,
        is_free=True,
        age_suitability="Ages 0–18 months",
        description="Bounces, tickles, and board books for the youngest readers.",
        url="https://multcolib.org/events",
    ),
    _Template(
        title="Science Playdate (Drop-in)",
        venue=_OMSI,
        at=time(10, 0),
        duration_minutes=120,
        is_free=False,
        age_suitability="Ages 0–6",
        description="Hands-on sensory and science stations geared to preschoolers.",
        url="https://omsi.edu/calendar/",
    ),
    _Template(
        title="Family Nature Walk",
        venue=_OREGON_ZOO,
        at=time(9, 30),
        duration_minutes=60,
        is_free=False,
        age_suitability="All ages",
        description="A short, stroller-friendly guided loop to meet a few animals.",
        url="https://www.oregonzoo.org/visit/events",
        weekdays=(5, 6),  # weekends only
    ),
    _Template(
        title="Playground Meetup",
        venue=_GRANT_PARK,
        at=time(15, 0),
        duration_minutes=90,
        is_free=True,
        age_suitability="Toddlers & preschoolers",
        description="Informal parent meetup at the playground — bring snacks and bubbles.",
        url="https://www.pdxparent.com/calendar/",
    ),
)

# Suffix that makes it unmistakable in the UI that this isn't live data.
_SAMPLE_SUFFIX = " (sample)"


def _instantiate(template: _Template, day: date) -> Activity:
    start = datetime.combine(day, template.at)
    end = start + timedelta(minutes=template.duration_minutes)
    return Activity(
        title=template.title + _SAMPLE_SUFFIX,
        source=SampledPortlandSource.name,
        start=start,
        end=end,
        description=template.description,
        url=template.url,
        is_free=template.is_free,
        age_suitability=template.age_suitability,
        location_name=template.venue.name,
        address=template.venue.address,
        lat=template.venue.lat,
        lon=template.venue.lon,
    )


class SampledPortlandSource(Source):
    """Placeholder Portland source so the pipeline works before real adapters exist."""

    name = "Sample data (placeholder)"
    region = REGION

    def fetch(self, window: SearchWindow) -> list[Activity]:
        activities: list[Activity] = []
        for day in window.dates:
            for template in _TEMPLATES:
                if template.weekdays and day.weekday() not in template.weekdays:
                    continue
                activities.append(_instantiate(template, day))
        return activities

"""The search engine: coarse location + days -> a sorted list of nearby activities.

This is the heart of the app and the one place that orchestrates every other module:

1. **Geocode** the coarse location to a center point.
2. **Fetch** from every source for the chosen region, *isolating failures* so one broken
   source never breaks the search (graceful degradation).
3. **Filter** to the chosen days and to within the search radius.
4. **Sort** by start time, then distance.

Source fetches are cached in-memory for a short TTL (keyed by source + dates), so changing
the radius or re-running a search within a couple of minutes doesn't re-hit the network.
Nothing is persisted to disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .cache import TTLCache
from .distance import haversine_miles
from .geocoding import GeocodeResult, geocode
from .models import Activity
from .sources import DEFAULT_REGION, get_sources
from .sources.base import Source
from .timewindow import Day, SearchWindow

DEFAULT_RADIUS_MILES = 10.0

# Short-lived cache of each source's fetch, keyed by (source name, window dates).
_FETCH_TTL_SECONDS = 120
_fetch_cache: TTLCache[tuple[str, tuple], list[Activity]] = TTLCache(_FETCH_TTL_SECONDS)


@dataclass(frozen=True)
class SourceError:
    """Records that a source failed, so the UI can be transparent about gaps."""

    source: str
    message: str


@dataclass
class SearchResult:
    """Everything a caller needs to render a search, including partial-failure info."""

    center: GeocodeResult
    window: SearchWindow
    radius_miles: float
    activities: list[Activity]
    errors: list[SourceError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when every source returned without error."""
        return not self.errors


def _fetch_source(source: Source, window: SearchWindow) -> list[Activity]:
    """Fetch a single source's activities, using the short-lived cache."""
    key = (source.name, window.dates)
    return _fetch_cache.get_or_compute(key, lambda: source.fetch(window))


def _within_radius(activity: Activity, center: GeocodeResult, radius_miles: float) -> bool:
    """Distance gate. Activities without coordinates can't be measured, so we keep them
    (better to show an unplaceable item than silently drop it) and sort them last."""
    if not activity.has_coordinates:
        return True
    activity.distance_miles = haversine_miles(
        center.lat, center.lon, activity.lat, activity.lon
    )
    return activity.distance_miles <= radius_miles


def _sort_key(activity: Activity) -> tuple:
    # Known start times first (chronological); then nearer before farther. Unknown
    # values sort last via the leading boolean flags.
    start = activity.start
    distance = activity.distance_miles
    return (
        start is None,
        start.timestamp() if start is not None else 0.0,
        distance is None,
        distance if distance is not None else 0.0,
    )


def search(
    location_query: str,
    days: list[Day],
    *,
    radius_miles: float = DEFAULT_RADIUS_MILES,
    region: str = DEFAULT_REGION,
    today=None,
) -> SearchResult:
    """Run a full search and return a :class:`SearchResult`.

    Raises :class:`~kids_activities_finder.geocoding.GeocodingError` if the location can't
    be resolved — that's the one failure we can't degrade around, since everything else
    depends on the center point. Individual source failures are captured in
    :attr:`SearchResult.errors`, not raised.
    """
    if not days:
        raise ValueError("Select at least one day to search.")

    center = geocode(location_query)
    window = SearchWindow.from_days(days, today=today)

    activities: list[Activity] = []
    errors: list[SourceError] = []

    for source in get_sources(region):
        try:
            fetched = _fetch_source(source, window)
        except Exception as exc:  # noqa: BLE001 - isolate any source failure
            errors.append(SourceError(source=source.name, message=str(exc)))
            continue
        for activity in fetched:
            if not window.includes(activity.start):
                continue
            if not _within_radius(activity, center, radius_miles):
                continue
            activities.append(activity)

    activities.sort(key=_sort_key)
    return SearchResult(
        center=center,
        window=window,
        radius_miles=radius_miles,
        activities=activities,
        errors=errors,
    )

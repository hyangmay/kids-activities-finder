"""Region-scoped registry of data sources.

Sources are grouped by region. The search engine asks for the sources covering a region
and fans out across them. Adding a new city = registering its sources here (and writing
the adapters); the core search/UI code doesn't change.
"""

from __future__ import annotations

from .base import Source
from .bibliocommons import BiblioCommonsSource

PORTLAND = "Portland, OR"


def _wccls() -> BiblioCommonsSource:
    """Washington County Cooperative Library Services (BiblioCommons).

    One feed covering Beaverton, Tigard, Tualatin, Hillsboro, and ~a dozen more
    Portland-metro branches.
    """
    return BiblioCommonsSource(
        slug="wccls",
        name="Washington County libraries (WCCLS)",
        region=PORTLAND,
        event_base_url="https://wccls.bibliocommons.com/events",
    )


# Maps a region name -> the sources that cover it. Real adapters get appended here as
# they're built; adding a new city means adding its sources without touching the core.
_REGISTRY: dict[str, list[Source]] = {
    PORTLAND: [_wccls()],
}

#: The default region until users can pick their own (see CLAUDE.md "still open").
DEFAULT_REGION = PORTLAND


def get_sources(region: str = DEFAULT_REGION) -> list[Source]:
    """Return the source instances covering ``region`` (empty list if none)."""
    return list(_REGISTRY.get(region, []))


def available_regions() -> list[str]:
    """Region names that currently have at least one source."""
    return sorted(_REGISTRY)


__all__ = [
    "Source",
    "DEFAULT_REGION",
    "get_sources",
    "available_regions",
]

"""Region-scoped registry of data sources.

Sources are grouped by region. The search engine asks for the sources covering a region
and fans out across them. Adding a new city = registering its sources here (and writing
the adapters); the core search/UI code doesn't change.
"""

from __future__ import annotations

from .base import Source
from .sample import REGION as PORTLAND, SampledPortlandSource

# Maps a region name -> the sources that cover it.
#
# Today this holds only a placeholder sample source for Portland (real Portland sites are
# JS-rendered with no stable feeds, so each real adapter is a separate effort). Real
# sources get appended to the Portland list as they're built; the sample is removed once
# at least one real source is live.
_REGISTRY: dict[str, list[Source]] = {
    PORTLAND: [SampledPortlandSource()],
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

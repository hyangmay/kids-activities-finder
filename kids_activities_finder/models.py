"""Normalized data model that every data source maps into.

Keeping a single shared shape means the UI and search logic never need to know which
source an activity came from.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Activity:
    """A single activity/event, normalized across all sources."""

    # --- Required ---
    title: str
    source: str  # which source produced this (e.g. "Multnomah County Library")

    # --- When ---
    start: datetime | None = None
    end: datetime | None = None

    # --- What ---
    description: str = ""
    url: str = ""  # link to the original listing
    is_free: bool | None = None  # None = unknown
    age_suitability: str = ""  # free-text, e.g. "Ages 0-3", "All ages"

    # --- Where ---
    location_name: str = ""  # venue name, e.g. "Sellwood Library"
    address: str = ""
    lat: float | None = None
    lon: float | None = None

    # --- Computed at search time ---
    distance_miles: float | None = None  # from the user's chosen center point

    @property
    def has_coordinates(self) -> bool:
        return self.lat is not None and self.lon is not None

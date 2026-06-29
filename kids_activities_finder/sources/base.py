"""The common interface every data source implements.

Sources are the most fragile part of the system (sites and APIs change), so they live
behind this small, stable contract. The search engine only ever sees normalized
:class:`~kids_activities_finder.models.Activity` objects and never needs to know whether
they came from a library calendar, a museum, or an aggregator API.

A source is **region-scoped**: it declares which region it covers (e.g. "Portland, OR").
Adding a new city means adding sources for that city — nothing in the core changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Activity
from ..timewindow import SearchWindow


class Source(ABC):
    """Base class for a region-scoped activity source.

    Subclasses set :attr:`name` and :attr:`region` and implement :meth:`fetch`.
    """

    #: Human-readable source name, surfaced in the UI (e.g. "Multnomah County Library").
    name: str = "Unnamed source"

    #: Region this source covers, e.g. "Portland, OR". Used to select sources per region.
    region: str = "Unknown"

    @abstractmethod
    def fetch(self, window: SearchWindow) -> list[Activity]:
        """Return activities for the given date window.

        Implementations should:

        * map their raw data into normalized :class:`Activity` objects,
        * set :attr:`Activity.source` to :attr:`name`,
        * limit to ``window`` where the upstream API allows it (the engine filters by
          date again as a safety net),
        * raise on hard failures — the search engine isolates the failure so one broken
          source never breaks the whole search.
        """

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Source {self.name!r} region={self.region!r}>"

"""The app's time horizon: today / tomorrow / day-after.

We deliberately keep this tiny and explicit. The user picks one or more of three
relative days; everything downstream works in terms of concrete ``date`` objects so
there's never any ambiguity about "what does tomorrow mean".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum


class Day(Enum):
    """A relative day the user can search."""

    TODAY = 0
    TOMORROW = 1
    DAY_AFTER = 2

    @property
    def label(self) -> str:
        return {0: "Today", 1: "Tomorrow", 2: "Day after"}[self.value]


# The full set, in display order.
ALL_DAYS: tuple[Day, ...] = (Day.TODAY, Day.TOMORROW, Day.DAY_AFTER)


def label_to_day(label: str) -> Day:
    """Map a UI label ("Today"/"Tomorrow"/"Day after") back to a :class:`Day`."""
    for day in ALL_DAYS:
        if day.label == label:
            return day
    raise ValueError(f"Unknown day label: {label!r}")


def resolve_dates(days: list[Day], *, today: date | None = None) -> list[date]:
    """Turn relative :class:`Day` choices into sorted, de-duplicated calendar dates."""
    base = today or date.today()
    dates = {base + timedelta(days=d.value) for d in days}
    return sorted(dates)


@dataclass(frozen=True)
class SearchWindow:
    """The concrete set of dates a search covers.

    Sources receive this so they can limit server-side queries to the date range, and
    the search engine uses it to drop activities that fall outside the chosen days.
    """

    dates: tuple[date, ...]

    @classmethod
    def from_days(cls, days: list[Day], *, today: date | None = None) -> "SearchWindow":
        return cls(tuple(resolve_dates(days, today=today)))

    @property
    def start(self) -> date:
        return self.dates[0]

    @property
    def end(self) -> date:
        return self.dates[-1]

    def includes(self, when: datetime | date | None) -> bool:
        """Whether a start time falls on one of the selected days.

        Activities with no known start time (``None``) are treated as *not* in the
        window — we can't honestly place them on a given day.
        """
        if when is None:
            return False
        day = when.date() if isinstance(when, datetime) else when
        return day in self.dates

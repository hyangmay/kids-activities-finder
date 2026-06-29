from datetime import date

from kids_activities_finder.sources.sample import REGION, SampledPortlandSource
from kids_activities_finder.timewindow import ALL_DAYS, SearchWindow

# A Monday, so weekend-only templates are excluded on the first day.
MONDAY = date(2026, 6, 29)


def test_fetch_returns_activities_on_each_day():
    window = SearchWindow.from_days(list(ALL_DAYS), today=MONDAY)
    activities = SampledPortlandSource().fetch(window)
    assert activities, "sample source should produce activities"
    produced_days = {a.start.date() for a in activities}
    assert produced_days <= set(window.dates)


def test_all_activities_normalized():
    window = SearchWindow.from_days(list(ALL_DAYS), today=MONDAY)
    for a in SampledPortlandSource().fetch(window):
        assert a.source == SampledPortlandSource.name
        assert a.has_coordinates  # coords present so distance filtering works
        assert a.start is not None and a.end is not None
        assert "(sample)" in a.title  # clearly labeled as placeholder data


def test_region_constant():
    assert SampledPortlandSource.region == REGION

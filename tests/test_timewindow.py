from datetime import date, datetime

from kids_activities_finder.timewindow import (
    ALL_DAYS,
    Day,
    SearchWindow,
    label_to_day,
    resolve_dates,
)

TODAY = date(2026, 6, 28)


def test_resolve_dates_relative_to_given_today():
    dates = resolve_dates(list(ALL_DAYS), today=TODAY)
    assert dates == [date(2026, 6, 28), date(2026, 6, 29), date(2026, 6, 30)]


def test_resolve_dates_dedupes_and_sorts():
    dates = resolve_dates([Day.DAY_AFTER, Day.TODAY, Day.TODAY], today=TODAY)
    assert dates == [date(2026, 6, 28), date(2026, 6, 30)]


def test_label_round_trip():
    for day in ALL_DAYS:
        assert label_to_day(day.label) is day


def test_window_includes_only_selected_days():
    window = SearchWindow.from_days([Day.TODAY, Day.TOMORROW], today=TODAY)
    assert window.includes(datetime(2026, 6, 28, 10, 0)) is True
    assert window.includes(datetime(2026, 6, 29, 23, 59)) is True
    assert window.includes(datetime(2026, 6, 30, 0, 0)) is False


def test_window_excludes_unknown_start():
    window = SearchWindow.from_days(list(ALL_DAYS), today=TODAY)
    assert window.includes(None) is False


def test_window_start_and_end():
    window = SearchWindow.from_days(list(ALL_DAYS), today=TODAY)
    assert window.start == date(2026, 6, 28)
    assert window.end == date(2026, 6, 30)

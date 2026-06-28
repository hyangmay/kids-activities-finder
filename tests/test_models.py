from kids_activities_finder.models import Activity


def test_activity_minimal():
    a = Activity(title="Baby Story Time", source="Multnomah County Library")
    assert a.title == "Baby Story Time"
    assert a.has_coordinates is False


def test_activity_has_coordinates():
    a = Activity(title="x", source="y", lat=45.5, lon=-122.6)
    assert a.has_coordinates is True

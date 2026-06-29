from kids_activities_finder.distance import haversine_miles


def test_zero_distance():
    assert haversine_miles(45.5, -122.6, 45.5, -122.6) == 0.0


def test_known_distance_portland_to_seattle():
    # Portland, OR -> Seattle, WA is ~145 miles as the crow flies.
    miles = haversine_miles(45.5152, -122.6784, 47.6062, -122.3321)
    assert 140 <= miles <= 150


def test_symmetric():
    a = haversine_miles(45.46, -122.65, 45.54, -122.62)
    b = haversine_miles(45.54, -122.62, 45.46, -122.65)
    assert abs(a - b) < 1e-9

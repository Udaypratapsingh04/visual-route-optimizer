import pytest
from routeopt import haversine_m


def test_zero_distance():
    assert haversine_m(27.49, 77.67, 27.49, 77.67) == 0.0


def test_one_degree_latitude():
    # 1 degree of latitude is ~111.19 km everywhere
    assert haversine_m(0, 0, 1, 0) == pytest.approx(111_195, abs=50)


def test_one_degree_longitude_at_equator():
    assert haversine_m(0, 0, 0, 1) == pytest.approx(111_195, abs=50)


def test_longitude_shrinks_with_latitude():
    assert haversine_m(60, 0, 60, 1) == pytest.approx(111_195 * 0.5, rel=0.01)


def test_symmetry():
    a = haversine_m(28.6139, 77.2090, 19.0760, 72.8777)
    b = haversine_m(19.0760, 72.8777, 28.6139, 77.2090)
    assert a == pytest.approx(b)


def test_delhi_mumbai_great_circle():
    # Published great-circle distance is ~1,150 km
    d = haversine_m(28.6139, 77.2090, 19.0760, 72.8777) / 1000
    assert 1140 < d < 1160


# TODO (Day 3 deliverable): add 2-3 REAL ground-truth cases from your campus.
# Pick two gates/junctions, read the straight-line distance on Google Maps
# ("Measure distance"), and assert within ~1-2 %.

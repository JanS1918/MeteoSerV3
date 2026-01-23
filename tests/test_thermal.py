import math
from core.utils.thermal import mrt_from_radiation, mrt_from_radiation_with_solar


def test_mrt_increases_with_radiation():
    ta = 20.0
    mrt0 = mrt_from_radiation(ta, 0.0)
    mrt_high = mrt_from_radiation(ta, 800.0)
    assert mrt0 is not None and mrt_high is not None
    assert mrt_high > mrt0


def test_mrt_with_solar_vs_without():
    ta = 20.0
    total = 800.0
    mrt_no_sun = mrt_from_radiation(ta, total)
    mrt_with_sun = mrt_from_radiation_with_solar(ta, total, sun_altitude_deg=45.0)
    assert mrt_no_sun is not None and mrt_with_sun is not None
    assert mrt_with_sun >= mrt_no_sun


def test_mrt_direct_fraction_monotonic():
    ta = 20.0
    total = 600.0
    m_low = mrt_from_radiation_with_solar(ta, total, sun_altitude_deg=5.0)
    m_mid = mrt_from_radiation_with_solar(ta, total, sun_altitude_deg=30.0)
    m_high = mrt_from_radiation_with_solar(ta, total, sun_altitude_deg=60.0)
    assert m_low is not None and m_mid is not None and m_high is not None
    assert m_low <= m_mid <= m_high

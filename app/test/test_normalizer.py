import pytest

from astropy.time import Time, TimeDelta
import astropy.units as u
from ephemeris import get_position
from ..normalizer import normalize_hpc, jsonify_skycoord


def test_normalize():
    # Using RHESSI Flare 12070596 as the test subject
    # hpc_x = 515
    # hpc_y = -342
    coord = normalize_hpc(515, -342, "2012-07-05 13:01:46", "2012-07-05 13:01:46")
    assert pytest.approx(coord.Tx.value) == 523.6178
    assert pytest.approx(coord.Ty.value) == -347.7228


def test_off_disk():
    # RHESSI Flare 120705117
    # This flare is positioned off the solar disk
    # https://umbra.nascom.nasa.gov/rhessi/rhessi_extras/flare_images_v2/2012/07/05/20120705_0325_0330/hsi_20120705_0325_0330.html
    # (-883,-348)
    # 2012-07-05 03:29:06
    coord = normalize_hpc(-883, -348, "2012-07-05 03:29:06", "2012-07-05 03:29:06")
    assert pytest.approx(coord.Tx.value) == -897.7240
    assert pytest.approx(coord.Ty.value) == -353.8028


def test_jsonify_skycoord():
    # Use ephemeric to get a SkyCoord with multiple coordinates
    # Get sdo position
    start = Time("2025-01-01 00:00:00")
    result = jsonify_skycoord(get_position("sdo", start, Time("2025-01-01 12:00:00")))
    assert len(result) == 13
    # Asset there is a coordinate for each time point between start and end.
    for i, coord in enumerate(result):
        assert coord["time"] == str(start + TimeDelta(i * u.hour))

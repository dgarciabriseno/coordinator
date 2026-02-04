from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u
from sunpy.coordinates import frames, transform_with_sun_center
from sunpy.physics.differential_rotation import solar_rotate_coordinate
from typing import List, Dict

from frames import get_helioviewer_frame, get_earth_frame


def hgs2hpc(lat: float, lon: float, coord_time: Time, target: Time) -> SkyCoord:
    """
    Takes a coordinate in the Heliographic Stonyhurst coordinate system
    with an assumed earth observer, and returns the coordinate in
    Helioprojective coordinates as seen from Helioviewer at the given
    target time.

    Parameters
    ----------
    lat : float
        Latitude coordinate in degrees
    lon : float
        Longitude coordinate in degrees
    coord_time : Time
        Time when the lat/lon coordinates were measured
    target : Time
        Desired observation time
    """
    hv_frame = get_helioviewer_frame(target)

    with transform_with_sun_center():
        coord = SkyCoord(
            lon * u.deg,
            lat * u.deg,
            frame=frames.HeliographicStonyhurst(obstime=coord_time),
        )
        # First convert to an hpc coordinate
        earth_frame = get_earth_frame(coord_time)
        hpc = coord.transform_to(earth_frame)
        # Then apply the rotation as seen from Helioviewer
        return solar_rotate_coordinate(hpc, hv_frame.observer)


def hgs2hpc_batch(coordinates: List[Dict], target: Time) -> List[Dict]:
    """
    Batch process multiple HGS to HPC coordinate transformations

    Parameters
    ----------
    coordinates : List[Dict]
        List of coordinate dictionaries with keys: lat, lon, coord_time
    target : Time
        Target observation time (same for all coordinates)

    Returns
    -------
    List[Dict]
        List of results with keys: x, y
    """
    if not coordinates:
        return []

    hv_frame = get_helioviewer_frame(target)

    with transform_with_sun_center():
        lats = [c["lat"] for c in coordinates]
        lons = [c["lon"] for c in coordinates]
        coord_time = [c["coord_time"] for c in coordinates]
        coord = SkyCoord(
            lons,
            lats,
            unit="deg,deg",
            frame=frames.HeliographicStonyhurst,
            obstime=coord_time,
        )
        # First convert to an hpc coordinate
        earth_frame = get_earth_frame(coord_time)
        hpc = coord.transform_to(earth_frame)
        # Then apply the rotation as seen from Helioviewer
        result = solar_rotate_coordinate(hpc, hv_frame.observer)
    return [{"x": c.Tx.value.item(), "y": c.Ty.value.item()} for c in result]

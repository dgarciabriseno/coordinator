from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u
from sunpy.coordinates import (
    transform_with_sun_center,
    GeocentricSolarEcliptic,
)
from sunpy.coordinates.screens import SphericalScreen
from sunpy.physics.differential_rotation import solar_rotate_coordinate
from frames import get_helioviewer_frame, get_earth_frame, get_3d_frame


def normalize_hpc(x: float, y: float, coord_time: Time, target: Time) -> SkyCoord:
    """
    Accepts a Helioprojective coordinate which is assumed to be measured
    at the given observation time from Earth, and transforms it to
    Helioviewer's point of view

    Parameters
    ----------
    x: float
        X coordinate in arcseconds
    y: float
        Y coordinate in arcseconds
    coord_time: Time
        Observation time of the given coordinates
    target: Time
        Desired time for the new coordinates
    """
    with transform_with_sun_center():
        earth_frame = get_earth_frame(coord_time)
        hv_frame = get_helioviewer_frame(target)
        with SphericalScreen(earth_frame.observer, only_off_disk=True):
            real_coord = SkyCoord(
                x * u.arcsecond, y * u.arcsecond, frame=earth_frame
            )
            return solar_rotate_coordinate(real_coord, hv_frame.observer)


def normalize_hpc_batch(coordinates: List[Dict], target: Time) -> List[Dict]:
    """
    Batch process multiple HPC coordinate normalizations

    Parameters
    ----------
    coordinates : List[Dict]
        List of coordinate dictionaries with keys: x, y, coord_time
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
        xs = [c["x"] for c in coordinates]
        ys = [c["y"] for c in coordinates]
        coord_times = [c["coord_time"] for c in coordinates]
        earth_frame = get_earth_frame(coord_times)
        with SphericalScreen(earth_frame.observer, only_off_disk=True):
            real_coord = SkyCoord(
                xs,
                ys,
                unit="arcsec,arcsec",
                frame=earth_frame,
            )
            result = solar_rotate_coordinate(real_coord, hv_frame.observer)
    return [{"x": c.Tx.value.item(), "y": c.Ty.value.item()} for c in result]


def skycoord_to_3dframe(coord: SkyCoord) -> SkyCoord:
    """
    Accepts a SkyCoord and transforms it to
    hv's unified coordinate frame

    Parameters
    ----------
    coord: SkyCoord
    """
    with transform_with_sun_center():
        return coord.transform_to(get_3d_frame())


def gse_frame(x: float, y: float, z: float, time: Time) -> dict:
    """
    Accepts a Geocentric Solar Ecliptic system coordinate and transforms it to
    hv's unified coordinate frame

    Parameters
    ----------
    x: float
        X coordinate in kilometers
    y: float
        Y coordinate in kilometers
    z: float
        Y coordinate in kilometers
    time: Time
        Coordinate time
    """
    real_coord = GeocentricSolarEcliptic(
        x * u.km, y * u.km, z * u.km, obstime=time, representation_type="cartesian"
    )
    return _normalize_skycoord(real_coord)


def jsonify_skycoord(coord: SkyCoord) -> list:
    """
    Converts the skycoord to a dict in kilometers after transforming it into
    the standard 3D frame.
    """
    return list(map(_normalize_skycoord, coord))


def _normalize_skycoord(coord: SkyCoord) -> dict:
    """
    Converts a skycoord to a normalized x,y,z,time dict.
    """
    with transform_with_sun_center():
        time = coord.obstime
        reframed = coord.transform_to(get_3d_frame())
        reframed.representation_type = "cartesian"
        return {
            "x": reframed.x.to("km").value,
            "y": reframed.y.to("km").value,
            "z": reframed.z.to("km").value,
            "time": str(time),
        }

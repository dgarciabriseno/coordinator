from typing import Annotated, List, Union

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import Field

from hgs2hpc import hgs2hpc
from normalizer import normalize_hpc, gse_frame, jsonify_skycoord
from ephemeris import get_position
from validation import AstropyTime, HvBaseModel

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class Hgs2HpcQueryParameters(HvBaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float
    coord_time: AstropyTime
    # Defaults to coord_time via constructor if None
    target: Union[AstropyTime, None] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.target is None:
            self.target = self.coord_time


@app.get(
    "/hgs2hpc",
    summary="Convert Heliographic Stonyhurst coordinate to Helioprojective coordinate in Helioviewer's POV",
)
# def _hgs2hpc(lat: float, lon: float, coord_time: str, target: Union[str, None] = None):
def _hgs2hpc(params: Annotated[Hgs2HpcQueryParameters, Query()]):
    "Convert a latitude/longitude coordinate to the equivalent helioprojective coordinate at the given target time"
    #    try:
    coord = hgs2hpc(params.lat, params.lon, params.coord_time, params.target)
    return {"x": coord.Tx.value, "y": coord.Ty.value}


class NormalizeHpcQueryParameters(HvBaseModel):
    x: float
    y: float
    coord_time: AstropyTime
    # Defaults to coord_time via constructor if None
    target: Union[AstropyTime, None] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.target is None:
            self.target = self.coord_time


@app.get("/hpc", summary="Get HPC coordinate for Helioviewer POV")
def _normalize_hpc(params: Annotated[NormalizeHpcQueryParameters, Query()]):
    coord = normalize_hpc(params.x, params.y, params.coord_time, params.target)
    return {"x": coord.Tx.value, "y": coord.Ty.value}


class GSECoordInput(HvBaseModel):
    x: float
    y: float
    z: float
    time: AstropyTime


class GSEInput(HvBaseModel):
    coordinates: List[GSECoordInput]


@app.post("/gse2frame", summary="Convert GSE coordinates to Helioviewer 3D coordinates")
def _normalize_gse(params: GSEInput):
    coords = map(lambda c: gse_frame(c.x, c.y, c.z, c.time), params.coordinates)
    return {"coordinates": list(coords)}


class PositionInput(HvBaseModel):
    start: AstropyTime
    stop: AstropyTime


@app.get("/position/{observatory}")
def _get_position(observatory: str, start: AstropyTime, stop: AstropyTime):
    return {"coordinates": jsonify_skycoord(get_position(observatory, start, stop))}


@app.get("/health-check", include_in_schema=False)
def health_check():
    """
    Performs a simple self test to make sure functions used will run
    without exceptions
    """
    normalize_hpc(515, -342, "2012-07-05 13:01:46", "2012-07-05 13:01:46")
    hgs2hpc(9, 9, "2024-01-01", "2024-01-02")
    gse_frame(0, 0, 0, "2024-01-02")
    return "success"

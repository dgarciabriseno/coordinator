from flask import Flask, request
from pydantic import ValidationError, Field

from hgs2hpc import hgs2hpc
from normalizer import normalize_hpc
from validation import AstropyTime, HvBaseModel

app = Flask("Helioviewer")


class Hgs2HpcQueryParameters(HvBaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float
    event_time: AstropyTime
    # Defaults to event_time via constructor if None
    target: AstropyTime = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.target is None:
            self.target = self.event_time


@app.route("/hgs2hpc", methods=["GET"])
def _hgs2hpc():
    try:
        params = Hgs2HpcQueryParameters(**request.args)
        coord = hgs2hpc(params.lat, params.lon, params.event_time, params.target)
        return {"x": coord.Tx.value, "y": coord.Ty.value}
    except ValidationError as e:
        return e.errors(include_context=False), 400


class NormalizeHpcQueryParameters(HvBaseModel):
    x: float
    y: float
    event_time: AstropyTime
    # Defaults to event_time via constructor if None
    target: AstropyTime = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.target is None:
            self.target = self.event_time


@app.route("/hpc", methods=["GET"])
def _normalize_hpc():
    try:
        params = NormalizeHpcQueryParameters(**request.args)
        coord = normalize_hpc(params.x, params.y, params.event_time, params.target)
        return {"x": coord.Tx.value, "y": coord.Ty.value}
    except ValidationError as e:
        return e.errors(include_context=False), 400


@app.route("/flask-health-check")
def flask_health_check():
    """
    Performs a simple self test to make sure functions used will run
    without exceptions
    """
    normalize_hpc(515, -342, "2012-07-05 13:01:46", "2012-07-05 13:01:46")
    hgs2hpc(9, 9, "2024-01-01", "2024-01-02")
    return "success"

# Coordinate
This python-based http API supports the main Helioviewer API
(PHP) by providing interfaces to functions written in python.

This allows Helioviewer to take advantage of libraries
in the python ecosystem (i.e. sunpy, astropy) without needing
to fully migrate the Helioviewer back-end to python. The
API is meant to run in parallel with Helioviewer.

## Usage
Running with docker:
```
docker run --rm -t ghcr.io/helioviewer-project/coordinator
```

Running manually with python
```
pip install -r requirements.txt
python -m fastapi run main.py
```

## Routes

The server hosts the following routes

### GET /hgs2hpc

Convert a heliographic stonyhurst coordinate into a helioprojective coordinate.

| query parameter | description |
|-----------------|-------------|
| lat             | Latitude coordinate in degrees |
| lon             | Longitude coordinate in degrees |
| coord_time      | Time that the measurement was taken |
| target          | (Optional) Desired observation time. Applies differential rotation |

Returns:
```
{ x: float, y: float }
```

### GET /hpc

Normalize a helioprojective coordinate into Helioviewer's coordinate frame.

| query parameter | description |
|-----------------|-------------|
| x               | X position in arcseconds |
| y               | Y position in arcseconds |
| coord_time      | Time that the measurement was taken |
| target          | (Optional) Desired observation time. Applies differential rotation |

Returns:
```
{ x: float, y: float }
```

### POST /gse

Transforms a list of GSE coordinates to Heliographic Stonyhurst coordinates using
a constant frame of reference. The reference frame is the coordinate frame used
for Heliographic Stonyhurst at 2025-01-01 00:00:00 UTC. All coordinate
transformations are done using sunpy and assume the sun remains at the origin
of the system.

```json
{
    "coordinates": [
        {
            "x": number in kilometers,
            "y": number in kilometers,
            "z": number in kilometers,
            "time": string (Y-m-d H:M:S)
        },
        ...
    ]
}
```


Returns the same format, but with the point in the new coordinate frame
```json
{
    "coordinates": [
        {
            "x": number,
            "y": number,
            "z": number,
            "time: string (Y-m-d H:M:S)
        },
        ...
    ]
}
```

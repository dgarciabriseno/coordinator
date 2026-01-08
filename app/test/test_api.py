import pytest
from astropy import units as u
from fastapi.testclient import TestClient
from sunpy.coordinates import get_earth

from ..main import app
from frames import get_3d_frame_date


@pytest.fixture
def client():
    return TestClient(app)


def test_hpc(client: TestClient):
    # Missing x
    response = client.get("/hpc?y=0&coord_time=2012-01-01")
    assert response.status_code == 422
    # Missing y
    response = client.get("/hpc?x=0&coord_time=2012-01-01")
    assert response.status_code == 422
    # Missing coord_time
    response = client.get("/hpc?x=0&y=0")
    assert response.status_code == 422

    # Using RHESSI Flare 12070596 as the test subject
    # hpc_x = 515
    # hpc_y = -342
    response = client.get("/hpc?x=515&y=-342&coord_time=2012-07-05+13:01:46")
    assert response.status_code == 200
    coord = response.json()
    assert pytest.approx(coord["x"]) == 523.6178
    assert pytest.approx(coord["y"]) == -347.7228

    # Test invalid time
    response = client.get("/hgs2hpc?lat=0&lon=0&coord_time=NotATime")
    print(response.json())
    assert response.status_code != 500

    # Converting to target time
    response = client.get(
        "/hpc?x=0&y=0&coord_time=2012-01-01 00:00:00&target=2012-01-01 01:00:00"
    )
    assert response.status_code == 200
    coord = response.json()
    # The x coordinate is expected to move to the right approximately 9 arcseconds
    assert 9 < coord["x"] and coord["x"] < 10


def test_hpc_post(client: TestClient):
    """
    Test POST /hpc endpoint with batch coordinate normalization
    """
    # Test valid batch request using RHESSI Flare 12070596
    batch_data = {
        "coordinates": [
            {"x": 515, "y": -342, "coord_time": "2012-07-05T13:01:46"},
            {"x": 100, "y": 200, "coord_time": "2012-07-05T13:02:00"},
        ],
        "target": "2012-07-05T13:01:46",
    }
    response = client.post("/hpc", json=batch_data)
    assert response.status_code == 200
    data = response.json()
    assert "coordinates" in data
    assert len(data["coordinates"]) == 2
    # First coordinate should match the known RHESSI flare result
    assert pytest.approx(data["coordinates"][0]["x"], abs=0.1) == 523.6178
    assert pytest.approx(data["coordinates"][0]["y"], abs=0.1) == -347.7228

    # Test with differential rotation (target time different from coord_time)
    batch_data = {
        "coordinates": [
            {"x": 0, "y": 0, "coord_time": "2012-01-01T00:00:00"},
        ],
        "target": "2012-01-01T01:00:00",
    }
    response = client.post("/hpc", json=batch_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["coordinates"]) == 1
    # The x coordinate should move approximately 9 arcseconds
    assert 9 < data["coordinates"][0]["x"] and data["coordinates"][0]["x"] < 10

    # Test missing coordinates field
    response = client.post("/hpc", json={"target": "2012-01-01T00:00:00Z"})
    assert response.status_code == 422

    # Test missing target field
    response = client.post(
        "/hpc",
        json={"coordinates": [{"x": 0, "y": 0, "coord_time": "2012-01-01T00:00:00Z"}]},
    )
    assert response.status_code == 422

    # Test invalid time format
    batch_data = {
        "coordinates": [{"x": 0, "y": 0, "coord_time": "NotAValidTime"}],
        "target": "2012-01-01T00:00:00Z",
    }
    response = client.post("/hpc", json=batch_data)
    assert response.status_code == 422

    # Test empty coordinates array
    batch_data = {"coordinates": [], "target": "2012-01-01T00:00:00Z"}
    response = client.post("/hpc", json=batch_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["coordinates"]) == 0

    # Test multiple coordinates with different coord_times
    batch_data = {
        "coordinates": [
            {"x": 100, "y": 200, "coord_time": "2024-01-01T00:00:00"},
            {"x": -300, "y": 450, "coord_time": "2025-01-01T00:00:00"},
            {"x": 500, "y": -100, "coord_time": "2022-01-01T00:00:00"},
        ],
        "target": "2024-01-02T00:00:00",
    }
    response = client.post("/hpc", json=batch_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["coordinates"]) == 3
    # Verify all coordinates have x and y values
    for coord in data["coordinates"]:
        assert "x" in coord
        assert "y" in coord
        assert isinstance(coord["x"], (int, float))
        assert isinstance(coord["y"], (int, float))

    # Test batch results match individual GET results
    batch_data = {
        "coordinates": [
            {"x": 515, "y": -342, "coord_time": "2012-07-05T13:01:46"},
        ],
        "target": "2012-07-05T13:01:46",
    }
    batch_response = client.post("/hpc", json=batch_data)
    individual_response = client.get(
        "/hpc?x=515&y=-342&coord_time=2012-07-05T13:01:46&target=2012-07-05T13:01:46"
    )
    assert batch_response.status_code == 200
    assert individual_response.status_code == 200
    batch_coord = batch_response.json()["coordinates"][0]
    individual_coord = individual_response.json()
    assert pytest.approx(batch_coord["x"], abs=1e-10) == individual_coord["x"]
    assert pytest.approx(batch_coord["y"], abs=1e-10) == individual_coord["y"]


def test_hgs2hpc(client: TestClient):
    # Missing lat
    response = client.get("/hgs2hpc?lon=0&coord_time=2012-01-01")
    assert response.status_code == 422
    # Missing lon
    response = client.get("/hgs2hpc?lat=0&coord_time=2012-01-01")
    assert response.status_code == 422
    # Missing coord_time
    response = client.get("/hgs2hpc?lat=0&lon=0")
    assert response.status_code == 422

    # Test invalid time
    response = client.get("/hgs2hpc?lat=0&lon=0&coord_time=NotATime")
    assert response.status_code == 422

    # Typical request, in this case expect that the hpc x coordinate is 0
    response = client.get("/hgs2hpc?lat=0&lon=0&coord_time=2012-01-01T00:00:00Z")
    assert response.status_code == 200
    coord = response.json()
    assert coord["x"] == 0

    # Same as the above request, but change the target time to 1 hour ahead
    # This should apply the differential rotation and the x coordinate should
    # move to the right approximately 9 arcseconds
    response = client.get(
        "/hgs2hpc?lat=0&lon=0&coord_time=2012-01-01 00:00:00&target=2012-01-01 01:00:00"
    )
    assert response.status_code == 200
    coord = response.json()
    assert 9 < coord["x"] and coord["x"] < 10

    # Verify correct status is returned when an invalid latitude longitude
    # coordinate is given. latitude/longitude must be between -90 and 90 inclusive.
    # Sunpy has no restriction on longitude, so all values are allowed
    # Test latitude is greater than 90
    response = client.get("/hgs2hpc?lat=90.1&lon=0&coord_time=2012-01-01 00:00:00")
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["loc"][1] == "lat"

    # Test latitude is less than -90
    response = client.get("/hgs2hpc?lat=-90.1&lon=0&coord_time=2012-01-01 00:00:00")
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["loc"][1] == "lat"


def test_hgs2hpc_post(client: TestClient):
    """
    Test POST /hgs2hpc endpoint with batch coordinate conversion
    """
    # Test valid batch request
    batch_data = {
        "coordinates": [
            {"lat": 0.0, "lon": 0.0, "coord_time": "2012-01-01T00:00:00Z"},
            {"lat": 10.0, "lon": 20.0, "coord_time": "2012-01-01T00:00:00Z"},
        ],
        "target": "2012-01-01T00:00:00Z",
    }
    response = client.post("/hgs2hpc", json=batch_data)
    assert response.status_code == 200
    data = response.json()
    assert "coordinates" in data
    assert len(data["coordinates"]) == 2
    assert pytest.approx(data["coordinates"][0]["x"], abs=0.1) == 0
    assert pytest.approx(data["coordinates"][0]["y"], abs=50) == 49.558
    assert pytest.approx(data["coordinates"][1]["x"], abs=0.1) == 324.471
    assert pytest.approx(data["coordinates"][1]["y"], abs=50) == 212.902

    # Test with differential rotation (target time different from coord_time)
    batch_data = {
        "coordinates": [
            {"lat": 0.0, "lon": 0.0, "coord_time": "2012-01-01T00:00:00Z"},
        ],
        "target": "2012-01-01T01:00:00Z",
    }
    response = client.post("/hgs2hpc", json=batch_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["coordinates"]) == 1
    # The x coordinate should move approximately 9 arcseconds
    assert 9 < data["coordinates"][0]["x"] and data["coordinates"][0]["x"] < 10

    # Test missing coordinates field
    response = client.post("/hgs2hpc", json={"target": "2012-01-01T00:00:00Z"})
    assert response.status_code == 422

    # Test missing target field
    response = client.post(
        "/hgs2hpc",
        json={
            "coordinates": [
                {"lat": 0.0, "lon": 0.0, "coord_time": "2012-01-01T00:00:00Z"}
            ]
        },
    )
    assert response.status_code == 422

    # Test invalid latitude (> 90)
    batch_data = {
        "coordinates": [
            {"lat": 90.1, "lon": 0.0, "coord_time": "2012-01-01T00:00:00Z"}
        ],
        "target": "2012-01-01T00:00:00Z",
    }
    response = client.post("/hgs2hpc", json=batch_data)
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["loc"][-1] == "lat"

    # Test invalid latitude (< -90)
    batch_data = {
        "coordinates": [
            {"lat": -90.1, "lon": 0.0, "coord_time": "2012-01-01T00:00:00Z"}
        ],
        "target": "2012-01-01T00:00:00Z",
    }
    response = client.post("/hgs2hpc", json=batch_data)
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["loc"][-1] == "lat"

    # Test invalid time format
    batch_data = {
        "coordinates": [{"lat": 0.0, "lon": 0.0, "coord_time": "NotAValidTime"}],
        "target": "2012-01-01T00:00:00Z",
    }
    response = client.post("/hgs2hpc", json=batch_data)
    assert response.status_code == 422

    # Test empty coordinates array
    batch_data = {"coordinates": [], "target": "2012-01-01T00:00:00Z"}
    response = client.post("/hgs2hpc", json=batch_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["coordinates"]) == 0

    # Test multiple coordinates with different coord_times
    batch_data = {
        "coordinates": [
            {"lat": 11.0, "lon": 21.0, "coord_time": "2024-01-01T00:00:00"},
            {"lat": 15.0, "lon": 26.0, "coord_time": "2025-01-01T00:00:00"},
            {"lat": 11.0, "lon": 21.0, "coord_time": "2022-01-01T00:00:00"},
        ],
        "target": "2024-01-02T00:00:00",
    }
    response = client.post("/hgs2hpc", json=batch_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["coordinates"]) == 3
    # Verify all coordinates have x and y values
    for coord in data["coordinates"]:
        assert "x" in coord
        assert "y" in coord
        assert isinstance(coord["x"], (int, float))
        assert isinstance(coord["y"], (int, float))


def test_healthcheck(client: TestClient):
    assert client.get("/health-check").text == '"success"'


def test_gse(client: TestClient):
    """
    Tests transforming GSE coordinates into the 3D frame.
    Test Steps:
      1. Use SDO position at the 3D frame's point in time.
      2. Convert that position to the 3D frame via the api
      3. SDO position should be very similar to earth position in the frame.
    """
    frame_date = get_3d_frame_date()
    date_str = frame_date.strftime("%Y-%m-%d %H:%M:%S")
    gse_coordinates = {
        "coordinates": [
            {
                # Position of SDO in GSE coordinates from
                # https://sscweb.gsfc.nasa.gov/WS/sscr/2/locations/sdo/20250101T000000Z,20250101T000200Z/gse/?resolutionFactor=2
                "x": 16856.9645,
                "y": 32613.5430,
                "z": -20740.0146,
                "time": date_str,
            }
        ]
    }
    response = client.post("/gse2frame", json=gse_coordinates)
    assert response.status_code == 200
    data = response.json()

    # Convert data to AU
    x_au = data["coordinates"][0]["x"] * u.km.to(u.AU)
    y_au = data["coordinates"][0]["y"] * u.km.to(u.AU)
    z_au = data["coordinates"][0]["z"] * u.km.to(u.AU)

    earth = get_earth(frame_date)
    earth.representation_type = "cartesian"
    assert abs(x_au - earth.x.value) < 0.001
    assert abs(y_au - earth.y.value) < 0.001
    assert abs(z_au - earth.z.value) < 0.001


def test_gse_errors(client: TestClient):
    """
    Test error scenarios for gse
    """
    # Test missing coordinates parameter
    response = client.post("/gse2frame", json="This is not json")
    assert response.status_code == 422

    # Test invalid JSON
    response = client.post("/gse2frame", content=b"invalid json")
    assert response.status_code == 422

    # Test missing required field
    response = client.post("/gse2frame", json={"coordinates": [{"x": 1, "y": 2}]})
    assert response.status_code == 422

    # Test invalid field type
    response = client.post(
        "/gse2frame", json={"coordinates": [{"x": "not a number", "y": 2, "z": 3}]}
    )
    assert response.status_code == 422

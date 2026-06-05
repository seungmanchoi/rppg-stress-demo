from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "mpsAvailable" in body
    assert "weightsLoaded" in body
    assert body["totalAlgorithms"] == 12


def test_algorithms_list():
    r = client.get("/api/v1/algorithms")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 12
    ids = {d["id"] for d in data}
    assert ids == {"POS", "CHROM", "OMIT", "GREEN", "ICA", "TS-CAN", "EfficientPhys",
                   "PhysFormer", "RhythmFormer", "BigSmall", "PhysNet", "DeepPhys"}


def test_get_nonexistent_measurement():
    r = client.get("/api/v1/measurements/nonexistent-id")
    assert r.status_code == 404


def test_post_measurement_rejects_missing_file():
    r = client.post("/api/v1/measurements")
    assert r.status_code == 422

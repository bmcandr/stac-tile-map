from api.main import app_factory
from fastapi.testclient import TestClient

client = TestClient(app_factory())


def test_default_map():
    resp = client.get("/map")
    assert resp.status_code == 200

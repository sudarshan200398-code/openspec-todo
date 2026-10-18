from fastapi.testclient import TestClient

from main import app


def test_root_serves_single_page() -> None:
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "daymark" in response.text

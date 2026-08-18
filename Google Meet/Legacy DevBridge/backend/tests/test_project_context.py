from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_validates_apps_script_project_context() -> None:
    response = client.post(
        "/api/v1/projects/context/validate",
        json={
            "script_id": "1AbCdEfGhIjKlMnOpQrStUvWxYz",
            "name": "  ATLAS  ",
            "editor_url": "https://script.google.com/home/projects/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit",
            "detected_at": "2026-08-18T00:00:00Z",
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == "ATLAS"
    assert response.json()["recognized"] is True


def test_rejects_non_apps_script_url() -> None:
    response = client.post(
        "/api/v1/projects/context/validate",
        json={
            "script_id": "1AbCdEfGhIjKlMnOpQrStUvWxYz",
            "name": "ATLAS",
            "editor_url": "https://example.com/projects/1AbCdEfGhIjKlMnOpQrStUvWxYz",
            "detected_at": "2026-08-18T00:00:00Z",
        },
    )
    assert response.status_code == 422

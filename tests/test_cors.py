from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cors_permite_el_origen_del_frontend():
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_no_permite_un_origen_desconocido():
    response = client.get("/health", headers={"Origin": "https://sitio-cualquiera.cl"})

    assert "access-control-allow-origin" not in response.headers

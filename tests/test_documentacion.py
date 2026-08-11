"""La documentacion de la API no se publica en produccion.

Con /docs, /redoc y /openapi.json abiertos, cualquiera desde internet lista las 18
rutas -las cuatro de /admin incluidas- y ve el nombre de la cabecera de administracion.
Para trabajar sirven; en produccion sobran.
"""

import pytest
from fastapi.testclient import TestClient

import app.config
from app.main import crear_app
from tests.conftest import ajustes

CLAVE_DE_PRODUCCION = "una-clave-de-produccion-larga-de-verdad-32"


@pytest.fixture
def como_en_produccion(monkeypatch):
    monkeypatch.setattr(
        app.config,
        "settings",
        ajustes(entorno="produccion", jwt_secret=CLAVE_DE_PRODUCCION),
    )


@pytest.mark.parametrize("ruta", ["/docs", "/redoc", "/openapi.json"])
def test_en_produccion_la_documentacion_no_se_publica(como_en_produccion, ruta):
    with TestClient(crear_app()) as prueba:
        assert prueba.get(ruta).status_code == 404


def test_en_produccion_la_api_sigue_respondiendo(como_en_produccion):
    """Cerrar la documentacion no puede cerrar la aplicacion."""
    with TestClient(crear_app()) as prueba:
        assert prueba.get("/health").status_code == 200


@pytest.mark.parametrize("ruta", ["/docs", "/openapi.json"])
def test_en_desarrollo_la_documentacion_sigue_a_mano(ruta):
    with TestClient(crear_app()) as prueba:
        assert prueba.get(ruta).status_code == 200


def test_el_contrato_se_puede_exportar_aunque_no_se_publique(como_en_produccion):
    """scripts/exportar_openapi.py arma el esquema desde el objeto, no por HTTP."""
    assert crear_app().openapi()["paths"]

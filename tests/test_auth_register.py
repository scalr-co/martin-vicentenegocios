"""Alta de un taller nuevo.

No es un registro publico: los talleres los das de alta tu. Por eso el endpoint pide
una clave de administracion que solo esta en las variables de entorno del servidor.
"""

import pytest

from app.config import Settings
from app.models import User, Workshop

CLAVE_ADMIN = "clave-de-administracion-de-solve"


@pytest.fixture(autouse=True)
def clave_de_admin_configurada(monkeypatch):
    """La clave se lee de `config.settings` en cada llamada, asi que basta con reemplazarla aca."""
    import app.config

    monkeypatch.setattr(app.config, "settings", Settings(admin_api_key=CLAVE_ADMIN))


def _alta(cliente, clave=CLAVE_ADMIN, **cambios):
    cuerpo = {
        "workshopName": "Taller San Cristobal",
        "workshopPhone": "56987654321",
        "ownerName": "Marcela",
        "email": "marcela@sancristobal.cl",
        "password": "una-clave-larga-de-verdad",
    }
    cuerpo.update(cambios)
    cabeceras = {"X-Admin-Key": clave} if clave is not None else {}
    return cliente.post("/auth/register", json=cuerpo, headers=cabeceras)


def test_el_alta_crea_el_taller_y_su_dueno(cliente, sesion):
    respuesta = _alta(cliente)

    assert respuesta.status_code == 201
    datos = respuesta.json()["data"]
    assert datos["workshop"]["name"] == "Taller San Cristobal"
    assert datos["user"]["role"] == "owner"
    assert sesion.query(Workshop).count() == 1
    assert sesion.query(User).count() == 1


def test_el_dueno_recien_creado_puede_entrar(cliente):
    _alta(cliente)

    respuesta = cliente.post(
        "/auth/login",
        json={"email": "marcela@sancristobal.cl", "password": "una-clave-larga-de-verdad"},
    )

    assert respuesta.status_code == 200


def test_sin_la_clave_de_administracion_no_se_puede_dar_de_alta(cliente, sesion):
    respuesta = _alta(cliente, clave=None)

    assert respuesta.status_code == 403
    assert sesion.query(Workshop).count() == 0


def test_con_una_clave_de_administracion_equivocada_tampoco(cliente, sesion):
    respuesta = _alta(cliente, clave="clave-inventada")

    assert respuesta.status_code == 403
    assert sesion.query(Workshop).count() == 0


def test_no_se_puede_repetir_el_correo_de_un_usuario(cliente, sesion):
    _alta(cliente)

    respuesta = _alta(cliente, workshopName="Otro Taller")

    assert respuesta.status_code == 409
    assert sesion.query(Workshop).count() == 1


def test_el_alta_no_devuelve_la_contrasena(cliente):
    respuesta = _alta(cliente)

    assert "una-clave-larga-de-verdad" not in respuesta.text
    assert "password" not in respuesta.text

"""La lista de estados sale de la API, no del frontend.

Si Martin los escribe a mano en su codigo, el dia que agreguemos o renombremos un estado
hay que acordarse de tocar dos repositorios. Con esto, uno.
"""

from app.models import ESTADOS
from tests.conftest import con_token, entrar


def test_devuelve_todos_los_estados_en_orden(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = cliente.get("/statuses", headers=con_token(token))

    assert respuesta.status_code == 200
    assert [e["key"] for e in respuesta.json()["data"]] == list(ESTADOS)


def test_cada_estado_trae_como_se_escribe_en_pantalla(cliente, dueno):
    """El frontend muestra la etiqueta; la clave es para el codigo."""
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = cliente.get("/statuses", headers=con_token(token))

    etiquetas = {e["key"]: e["label"] for e in respuesta.json()["data"]}
    assert etiquetas["en_diagnostico"] == "En diagnóstico"
    assert etiquetas["listo"] == "Listo"


def test_dice_cual_estado_cierra_la_orden(cliente, dueno):
    """Para que el panel sepa cuales pintar como abiertas sin adivinar."""
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = cliente.get("/statuses", headers=con_token(token))

    abiertos = {e["key"]: e["isOpen"] for e in respuesta.json()["data"]}
    assert abiertos["entregado"] is False
    assert abiertos["recibido"] is True


def test_sin_token_no_se_puede_consultar(cliente, dueno):
    respuesta = cliente.get("/statuses")

    assert respuesta.status_code == 401

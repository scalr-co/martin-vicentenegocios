"""Probar contrasenas una tras otra tiene que costar algo.

La auditoria hizo 20 intentos fallidos seguidos y recibio 20 veces 401: ni 429, ni
bloqueo, ni registro. El unico freno era lo que tarda bcrypt.
"""

import pytest

from app.security.intentos import LIMITE_POR_CUENTA, limpiar_todo
from tests.conftest import CLAVE_DE_PRUEBA, entrar


@pytest.fixture(autouse=True)
def sin_intentos_de_otros_tests():
    """El registro vive en la memoria del proceso: sin esto se filtra entre tests."""
    limpiar_todo()
    yield
    limpiar_todo()


def fallar(cliente, correo="dueno@taller.cl"):
    return cliente.post("/auth/login", json={"email": correo, "password": "la-que-no-es"})


def test_despues_de_varios_intentos_fallidos_el_login_se_cierra(cliente, dueno):
    for _ in range(LIMITE_POR_CUENTA):
        assert fallar(cliente).status_code == 401

    respuesta = fallar(cliente)

    assert respuesta.status_code == 429
    assert respuesta.json()["error"]["code"] == "TOO_MANY_REQUESTS"


def test_con_el_login_cerrado_no_sirve_ni_la_clave_correcta(cliente, dueno):
    """Si la clave correcta pasara igual, el freno no frenaria nada."""
    for _ in range(LIMITE_POR_CUENTA):
        fallar(cliente)

    respuesta = cliente.post(
        "/auth/login", json={"email": "dueno@taller.cl", "password": CLAVE_DE_PRUEBA}
    )

    assert respuesta.status_code == 429


def test_entrar_bien_borra_los_intentos_fallidos(cliente, dueno):
    """El que se equivoco tres veces y se acordo no arrastra esos tres toda la tarde."""
    for _ in range(LIMITE_POR_CUENTA - 1):
        fallar(cliente)

    entrar(cliente, "dueno@taller.cl")

    for _ in range(LIMITE_POR_CUENTA):
        respuesta = fallar(cliente)
    assert respuesta.status_code == 401


def test_el_freno_de_una_cuenta_no_deja_fuera_a_la_otra(cliente, dueno, mecanico):
    """En un taller todos entran desde la misma red: el vecino no puede pagar por otro."""
    for _ in range(LIMITE_POR_CUENTA + 1):
        fallar(cliente)

    respuesta = cliente.post(
        "/auth/login", json={"email": "mecanico@taller.cl", "password": CLAVE_DE_PRUEBA}
    )

    assert respuesta.status_code == 200

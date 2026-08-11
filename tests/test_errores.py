"""Todos los errores tienen que salir con la misma forma.

El frontend de Martin lee { error: { message, code } }. Si algunos errores salieran
con la forma de FastAPI ({ detail }), tendria que programar dos caminos distintos.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errores import registrar_manejadores
from tests.conftest import CLAVE_DE_PRUEBA, con_token, entrar


def test_un_error_de_credenciales_sale_con_la_forma_del_contrato(cliente, dueno):
    respuesta = cliente.post(
        "/auth/login",
        json={"email": "dueno@taller.cl", "password": "clave-mala"},
    )

    cuerpo = respuesta.json()
    assert list(cuerpo) == ["error"]
    assert set(cuerpo["error"]) == {"message", "code"}
    assert cuerpo["error"]["code"] == "UNAUTHORIZED"


def test_un_error_de_validacion_tambien_respeta_el_contrato(cliente):
    respuesta = cliente.post(
        "/auth/login",
        json={"email": "esto-no-es-un-correo", "password": CLAVE_DE_PRUEBA},
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"


def test_una_ruta_inexistente_responde_con_el_contrato(cliente):
    respuesta = cliente.get("/esta-ruta-no-existe")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "NOT_FOUND"


def test_un_error_no_previsto_tambien_respeta_el_contrato():
    """La red de seguridad: no importa que reviente, el frontend sabe leerlo.

    Sin esto, un bug cualquiera sale como "Internal Server Error" en texto plano y el
    frontend, que solo sabe leer {"error": {...}}, muestra basura.
    """
    aplicacion = FastAPI()
    registrar_manejadores(aplicacion)

    @aplicacion.get("/revienta")
    def revienta():
        raise RuntimeError("clave secreta adentro del mensaje")

    with TestClient(aplicacion, raise_server_exceptions=False) as prueba:
        respuesta = prueba.get("/revienta")

    assert respuesta.status_code == 500
    assert respuesta.json()["error"]["code"] == "INTERNAL_ERROR"


def test_un_error_no_previsto_no_le_cuenta_al_cliente_lo_que_paso():
    """Lo que se filtra en un error es lo que usa el que esta tanteando la API."""
    aplicacion = FastAPI()
    registrar_manejadores(aplicacion)

    @aplicacion.get("/revienta")
    def revienta():
        raise RuntimeError("clave secreta adentro del mensaje")

    with TestClient(aplicacion, raise_server_exceptions=False) as prueba:
        respuesta = prueba.get("/revienta")

    assert "clave secreta" not in respuesta.text
    assert "RuntimeError" not in respuesta.text


def test_una_pagina_absurda_se_rechaza_como_validacion(cliente, dueno):
    """El parametro tenia tope por abajo pero no por arriba, y reventaba con un 500."""
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = cliente.get(
        "/clients?page=999999999999999999999999", headers=con_token(token)
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"


def test_los_errores_no_dejan_escapar_la_palabra_detail(cliente, dueno):
    respuesta = cliente.post(
        "/auth/login",
        json={"email": "dueno@taller.cl", "password": "clave-mala"},
    )

    assert "detail" not in respuesta.json()

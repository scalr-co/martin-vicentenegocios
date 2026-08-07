"""Todos los errores tienen que salir con la misma forma.

El frontend de Martin lee { error: { message, code } }. Si algunos errores salieran
con la forma de FastAPI ({ detail }), tendria que programar dos caminos distintos.
"""

from tests.conftest import CLAVE_DE_PRUEBA


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


def test_los_errores_no_dejan_escapar_la_palabra_detail(cliente, dueno):
    respuesta = cliente.post(
        "/auth/login",
        json={"email": "dueno@taller.cl", "password": "clave-mala"},
    )

    assert "detail" not in respuesta.json()

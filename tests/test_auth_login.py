from tests.conftest import CLAVE_DE_PRUEBA


def test_login_correcto_devuelve_token_taller_y_usuario(cliente, dueno):
    respuesta = cliente.post(
        "/auth/login",
        json={"email": "dueno@taller.cl", "password": CLAVE_DE_PRUEBA},
    )

    assert respuesta.status_code == 200
    datos = respuesta.json()["data"]
    assert datos["token"]
    assert datos["workshop"]["name"] == "Taller Los Alerces"
    assert datos["user"]["email"] == "dueno@taller.cl"
    assert datos["user"]["role"] == "owner"


def test_el_login_nunca_devuelve_la_contrasena_guardada(cliente, dueno):
    respuesta = cliente.post(
        "/auth/login",
        json={"email": "dueno@taller.cl", "password": CLAVE_DE_PRUEBA},
    )

    assert "passwordHash" not in respuesta.text
    assert "password_hash" not in respuesta.text


def test_login_con_contrasena_incorrecta_es_rechazado(cliente, dueno):
    respuesta = cliente.post(
        "/auth/login",
        json={"email": "dueno@taller.cl", "password": "no-es-la-clave"},
    )

    assert respuesta.status_code == 401


def test_login_con_email_inexistente_da_el_mismo_error_que_la_clave_mala(cliente, dueno):
    """Si los mensajes fueran distintos, se podria averiguar que correos estan registrados."""
    clave_mala = cliente.post(
        "/auth/login",
        json={"email": "dueno@taller.cl", "password": "no-es-la-clave"},
    )
    email_inexistente = cliente.post(
        "/auth/login",
        json={"email": "nadie@taller.cl", "password": CLAVE_DE_PRUEBA},
    )

    assert email_inexistente.status_code == clave_mala.status_code
    assert email_inexistente.json() == clave_mala.json()


def test_un_usuario_desactivado_no_puede_entrar(cliente, sesion, dueno):
    dueno.active = False
    sesion.commit()

    respuesta = cliente.post(
        "/auth/login",
        json={"email": "dueno@taller.cl", "password": CLAVE_DE_PRUEBA},
    )

    assert respuesta.status_code == 401


def test_un_taller_desactivado_no_deja_entrar_a_su_gente(cliente, sesion, taller, dueno):
    """Sirve para suspender a un taller que deja de pagar sin borrarle los datos."""
    taller.active = False
    sesion.commit()

    respuesta = cliente.post(
        "/auth/login",
        json={"email": "dueno@taller.cl", "password": CLAVE_DE_PRUEBA},
    )

    assert respuesta.status_code == 401

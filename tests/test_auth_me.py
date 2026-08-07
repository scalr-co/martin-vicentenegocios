from app.security.tokens import crear_token
from tests.conftest import entrar


def test_me_devuelve_el_taller_y_el_usuario_del_token(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = cliente.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert respuesta.status_code == 200
    datos = respuesta.json()["data"]
    assert datos["user"]["email"] == "dueno@taller.cl"
    assert datos["user"]["role"] == "owner"
    assert datos["workshop"]["name"] == "Taller Los Alerces"


def test_me_sin_token_es_rechazado(cliente, dueno):
    respuesta = cliente.get("/auth/me")

    assert respuesta.status_code == 401


def test_me_con_un_token_inventado_es_rechazado(cliente, dueno):
    respuesta = cliente.get("/auth/me", headers={"Authorization": "Bearer no-es-un-token"})

    assert respuesta.status_code == 401


def test_un_token_de_un_usuario_que_ya_no_existe_es_rechazado(cliente, taller):
    """Un token firmado por nosotros no basta: el usuario tiene que seguir existiendo."""
    token = crear_token(user_id="usuario-borrado", workshop_id=taller.id, role="owner")

    respuesta = cliente.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert respuesta.status_code == 401


def test_un_token_de_un_usuario_desactivado_es_rechazado(cliente, sesion, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    dueno.active = False
    sesion.commit()

    respuesta = cliente.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert respuesta.status_code == 401

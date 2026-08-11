"""Cerrar una sesion abierta.

Antes no se podia: el token vivia 12 horas pasara lo que pasara. Lo unico que lo
cortaba era poner `active=False` en la base a mano, y cambiar la contrasena tampoco
invalidaba las sesiones ya abiertas. Al mecanico al que le roban el celular con la
sesion abierta, la respuesta honesta era "hay que esperar 12 horas".
"""

from sqlalchemy import select

from app.models import User
from tests.conftest import con_token, entrar
from tests.test_admin import alta_de_taller  # noqa: F401
from tests.test_admin import clave_de_admin_configurada  # noqa: F401  (fixture autouse)
from tests.test_admin import token_admin  # noqa: F401  (fixture)


def test_cerrar_las_sesiones_deja_fuera_al_token_viejo(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    assert cliente.get("/auth/me", headers=con_token(token)).status_code == 200

    cerrar = cliente.post("/auth/logout-all", headers=con_token(token))

    assert cerrar.status_code == 204
    assert cliente.get("/auth/me", headers=con_token(token)).status_code == 401


def test_despues_de_cerrarlas_se_puede_volver_a_entrar(cliente, dueno):
    """Cerrar sesiones no es desactivar la cuenta."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente.post("/auth/logout-all", headers=con_token(token))

    nuevo = entrar(cliente, "dueno@taller.cl")

    assert cliente.get("/auth/me", headers=con_token(nuevo)).status_code == 200


def test_cerrar_mis_sesiones_no_toca_las_de_otro_usuario(cliente, dueno, mecanico):
    token_dueno = entrar(cliente, "dueno@taller.cl")
    token_mecanico = entrar(cliente, "mecanico@taller.cl")

    cliente.post("/auth/logout-all", headers=con_token(token_dueno))

    assert cliente.get("/auth/me", headers=con_token(token_mecanico)).status_code == 200


def test_cambiarle_la_clave_al_dueno_corta_sus_sesiones_abiertas(cliente, token_admin, sesion):
    """El dueno perdio la clave, el admin se la cambia: la sesion vieja tiene que caer.

    Sin esto, quien tuviera el token de antes seguia adentro 12 horas mas.
    """
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]
    viejo = entrar(cliente, "marcela@sancristobal.cl", clave="una-clave-larga-de-verdad")

    cliente.post(
        f"/admin/workshops/{taller_id}/owner-password",
        json={"password": "la-clave-nueva-que-le-paso"},
        headers=con_token(token_admin),
    )

    assert cliente.get("/auth/me", headers=con_token(viejo)).status_code == 401


def test_un_token_con_una_version_de_sesion_vieja_no_sirve(cliente, dueno, sesion):
    """Lo mismo pero visto por dentro: el token lleva la version con la que se emitio."""
    token = entrar(cliente, "dueno@taller.cl")

    usuario = sesion.scalar(select(User).where(User.email == "dueno@taller.cl"))
    usuario.token_version += 1
    sesion.commit()

    assert cliente.get("/auth/me", headers=con_token(token)).status_code == 401


def test_sin_token_no_se_pueden_cerrar_sesiones(cliente, dueno):
    assert cliente.post("/auth/logout-all").status_code == 401

"""Lo que hace la administracion de la plataforma queda escrito.

La auditoria encontro que un admin podia cambiarle la clave al dueno de cualquier taller
y entrar a sus datos sin dejar rastro: `cambiar_clave_del_dueno` solo reescribia el hash.
Con tres personas con acceso, no habria forma de saber quien entro a que taller.
"""

from sqlalchemy import select

from app.models import (
    ACCION_CLAVE_DEL_DUENO_CAMBIADA,
    ACCION_TALLER_CREADO,
    ACCION_TALLER_EDITADO,
    AdminAudit,
    User,
)
from tests.conftest import con_token
from tests.test_admin import alta_de_taller  # noqa: F401  (usa el mismo cuerpo de alta)
from tests.test_admin import token_admin  # noqa: F401  (fixture)
from tests.test_admin import clave_de_admin_configurada  # noqa: F401  (fixture autouse)


def _admin(sesion) -> User:
    return sesion.scalar(select(User).where(User.email == "vicente@solve.cl"))


def test_dar_de_alta_un_taller_queda_registrado(cliente, token_admin, sesion):
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]

    registro = sesion.scalar(
        select(AdminAudit).where(AdminAudit.action == ACCION_TALLER_CREADO)
    )
    assert registro.actor_user_id == _admin(sesion).id
    assert registro.workshop_id == taller_id


def test_corregir_un_taller_queda_registrado_con_lo_que_se_toco(cliente, token_admin, sesion):
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]

    cliente.patch(
        f"/admin/workshops/{taller_id}",
        json={"name": "Taller San Cristobal Ltda"},
        headers=con_token(token_admin),
    )

    registro = sesion.scalar(
        select(AdminAudit).where(AdminAudit.action == ACCION_TALLER_EDITADO)
    )
    assert registro.workshop_id == taller_id
    assert registro.detail == "name"


def test_cambiarle_la_clave_al_dueno_queda_registrado(cliente, token_admin, sesion):
    """La accion mas delicada del panel: deja a una persona fuera de su propio sistema."""
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]
    dueno = sesion.scalar(select(User).where(User.email == "marcela@sancristobal.cl"))

    cliente.post(
        f"/admin/workshops/{taller_id}/owner-password",
        json={"password": "la-clave-nueva-que-le-paso"},
        headers=con_token(token_admin),
    )

    registro = sesion.scalar(
        select(AdminAudit).where(AdminAudit.action == ACCION_CLAVE_DEL_DUENO_CAMBIADA)
    )
    assert registro.actor_user_id == _admin(sesion).id
    assert registro.workshop_id == taller_id
    assert registro.target_user_id == dueno.id


def test_el_registro_no_se_puede_escribir_desde_la_api(cliente, token_admin):
    """No hay ruta que toque admin_audit: es un registro que solo crece por dentro."""
    assert cliente.post("/admin/audit", headers=con_token(token_admin)).status_code == 404
    assert cliente.get("/admin/audit", headers=con_token(token_admin)).status_code == 404

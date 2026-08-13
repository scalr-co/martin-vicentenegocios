"""Los planes del taller: lo que se vende y lo que el sistema deja hacer.

La landing y el panel venden dos planes: basico -hasta tres mecanicos- y plus, sin tope.
Hasta ahora ese limite vivia solo en `frontend/src/lib/plans.ts`, o sea en el navegador
del que mira la pantalla: un taller basico podia crear veinte mecanicos y nadie se
enteraba. Un tope que se cobra tiene que vivir en el servidor.
"""

from sqlalchemy import select

from app.models import ACCION_TALLER_EDITADO, AdminAudit
from app.models.workshop import PLAN_BASICO, PLAN_PLUS
from tests.conftest import con_token
from tests.test_admin import alta_de_taller
from tests.test_admin import clave_de_admin_configurada  # noqa: F401  (fixture autouse)
from tests.test_admin import token_admin  # noqa: F401  (fixture)

CLAVE_DEL_DUENO = "una-clave-larga-de-verdad"
CORREO_DEL_DUENO = "marcela@sancristobal.cl"


def _dar_de_alta(cliente, token_admin, **cambios) -> str:
    respuesta = alta_de_taller(cliente, token_admin, **cambios)
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["data"]["workshop"]["id"]


def test_un_taller_nace_en_el_plan_basico(cliente, token_admin):
    """El plan mas chico es el default: nadie recibe plus sin que alguien lo decida."""
    respuesta = alta_de_taller(cliente, token_admin)

    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["data"]["workshop"]["plan"] == PLAN_BASICO


def test_se_puede_dar_de_alta_directo_en_plus(cliente, token_admin):
    """El taller que llega pagando el plan grande no tiene que pasar por el chico."""
    respuesta = alta_de_taller(cliente, token_admin, plan=PLAN_PLUS)

    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["data"]["workshop"]["plan"] == PLAN_PLUS


def test_el_panel_sube_el_plan_y_queda_anotado(cliente, token_admin, sesion):
    """Cambiar el plan es cambiar lo que se cobra: tiene que quedar rastro de quien fue."""
    taller_id = _dar_de_alta(cliente, token_admin)

    respuesta = cliente.patch(
        f"/admin/workshops/{taller_id}",
        json={"plan": PLAN_PLUS},
        headers=con_token(token_admin),
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["data"]["plan"] == PLAN_PLUS

    anotado = sesion.scalar(
        select(AdminAudit).where(
            AdminAudit.action == ACCION_TALLER_EDITADO,
            AdminAudit.workshop_id == taller_id,
        )
    )
    assert anotado is not None
    assert "plan" in anotado.detail


def test_un_plan_inventado_no_entra_por_ninguna_de_las_dos_puertas(cliente, token_admin):
    """Vale lo que se vende y nada mas: un plan "oro" no lo entiende ni la facturacion."""
    taller_id = _dar_de_alta(cliente, token_admin)

    edicion = cliente.patch(
        f"/admin/workshops/{taller_id}",
        json={"plan": "oro"},
        headers=con_token(token_admin),
    )
    alta = alta_de_taller(cliente, token_admin, plan="oro", email="otra@sancristobal.cl")

    assert edicion.status_code == 422
    assert alta.status_code == 422


def test_el_plan_llega_en_el_login(cliente, token_admin):
    """Lo lee el panel del taller para saber que mostrar, asi que viaja con la sesion."""
    _dar_de_alta(cliente, token_admin, plan=PLAN_PLUS)

    respuesta = cliente.post(
        "/auth/login",
        json={"email": CORREO_DEL_DUENO, "password": CLAVE_DEL_DUENO},
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["data"]["workshop"]["plan"] == PLAN_PLUS


def test_la_ficha_de_soporte_muestra_el_plan(cliente, token_admin):
    """Es lo primero que se mira cuando el taller pregunta por que no puede sumar gente."""
    taller_id = _dar_de_alta(cliente, token_admin, plan=PLAN_PLUS)

    respuesta = cliente.get(
        f"/admin/workshops/{taller_id}", headers=con_token(token_admin)
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["data"]["plan"] == PLAN_PLUS

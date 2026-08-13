"""Los planes del taller: lo que se vende y lo que el sistema deja hacer.

La landing y el panel venden dos planes: basico -hasta tres mecanicos- y plus, sin tope.
Hasta ahora ese limite vivia solo en `frontend/src/lib/plans.ts`, o sea en el navegador
del que mira la pantalla: un taller basico podia crear veinte mecanicos y nadie se
enteraba. Un tope que se cobra tiene que vivir en el servidor.
"""

from sqlalchemy import select

from app.models import ACCION_TALLER_EDITADO, MAX_MECANICOS_BASICO, AdminAudit
from app.models.workshop import PLAN_BASICO, PLAN_PLUS
from tests.conftest import con_token, entrar
from tests.test_admin import alta_de_taller
from tests.test_admin import clave_de_admin_configurada  # noqa: F401  (fixture autouse)
from tests.test_admin import token_admin  # noqa: F401  (fixture)

CLAVE_DEL_DUENO = "una-clave-larga-de-verdad"
CORREO_DEL_DUENO = "marcela@sancristobal.cl"
CLAVE_DEL_MECANICO = "clave-del-mecanico"


def _dar_de_alta(cliente, token_admin, **cambios) -> str:
    respuesta = alta_de_taller(cliente, token_admin, **cambios)
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["data"]["workshop"]["id"]


def _taller_con_dueno_adentro(cliente, token_admin, **cambios) -> tuple[str, str]:
    """El taller recien creado y el token de su dueno, que es quien contrata."""
    taller_id = _dar_de_alta(cliente, token_admin, **cambios)
    return taller_id, entrar(cliente, CORREO_DEL_DUENO, clave=CLAVE_DEL_DUENO)


def _contratar(cliente, token_dueno, numero: int):
    """Un mecanico mas, dado de alta por el dueno como en la pantalla de Mecanicos."""
    return cliente.post(
        "/users",
        json={
            "name": f"Mecanico {numero}",
            "email": f"mecanico{numero}@sancristobal.cl",
            "password": CLAVE_DEL_MECANICO,
        },
        headers=con_token(token_dueno),
    )


def _llenar_el_cupo(cliente, token_dueno) -> list[str]:
    """Los tres mecanicos que caben en el plan basico."""
    ids = []
    for numero in range(1, MAX_MECANICOS_BASICO + 1):
        respuesta = _contratar(cliente, token_dueno, numero)
        assert respuesta.status_code == 201, respuesta.text
        ids.append(respuesta.json()["data"]["id"])
    return ids


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


def test_el_plan_basico_se_queda_en_tres_mecanicos(cliente, token_admin):
    """El dueno no ocupa cupo: son tres mecanicos ademas de el, como dice la landing."""
    _, token_dueno = _taller_con_dueno_adentro(cliente, token_admin)
    _llenar_el_cupo(cliente, token_dueno)

    respuesta = _contratar(cliente, token_dueno, MAX_MECANICOS_BASICO + 1)

    assert respuesta.status_code == 409, respuesta.text
    assert str(MAX_MECANICOS_BASICO) in respuesta.json()["error"]["message"]


def test_el_plan_plus_no_tiene_tope(cliente, token_admin):
    _, token_dueno = _taller_con_dueno_adentro(cliente, token_admin, plan=PLAN_PLUS)
    _llenar_el_cupo(cliente, token_dueno)

    respuesta = _contratar(cliente, token_dueno, MAX_MECANICOS_BASICO + 1)

    assert respuesta.status_code == 201, respuesta.text


def test_apagar_a_uno_deja_lugar_para_otro(cliente, token_admin):
    """El tope cuenta a los que estan trabajando, no a los que alguna vez trabajaron."""
    _, token_dueno = _taller_con_dueno_adentro(cliente, token_admin)
    primero, *_ = _llenar_el_cupo(cliente, token_dueno)

    apagado = cliente.patch(
        f"/users/{primero}", json={"active": False}, headers=con_token(token_dueno)
    )
    respuesta = _contratar(cliente, token_dueno, MAX_MECANICOS_BASICO + 1)

    assert apagado.status_code == 200, apagado.text
    assert respuesta.status_code == 201, respuesta.text


def test_reactivar_a_uno_de_mas_tampoco_se_puede(cliente, token_admin):
    """Sin esto el tope se salta con dos clicks: apagar, contratar y volver a encender."""
    _, token_dueno = _taller_con_dueno_adentro(cliente, token_admin)
    primero, *_ = _llenar_el_cupo(cliente, token_dueno)
    cliente.patch(
        f"/users/{primero}", json={"active": False}, headers=con_token(token_dueno)
    )
    assert _contratar(cliente, token_dueno, MAX_MECANICOS_BASICO + 1).status_code == 201

    respuesta = cliente.patch(
        f"/users/{primero}", json={"active": True}, headers=con_token(token_dueno)
    )

    assert respuesta.status_code == 409, respuesta.text


def test_bajar_de_plan_no_bota_a_nadie(cliente, token_admin):
    """Un taller que se pasa al plan chico no puede quedarse sin la gente que trabaja hoy.

    Sigue con sus cinco mecanicos y todos entran; lo unico que no puede es sumar al sexto.
    """
    taller_id, token_dueno = _taller_con_dueno_adentro(
        cliente, token_admin, plan=PLAN_PLUS
    )
    _llenar_el_cupo(cliente, token_dueno)
    for numero in (MAX_MECANICOS_BASICO + 1, MAX_MECANICOS_BASICO + 2):
        assert _contratar(cliente, token_dueno, numero).status_code == 201

    cliente.patch(
        f"/admin/workshops/{taller_id}",
        json={"plan": PLAN_BASICO},
        headers=con_token(token_admin),
    )

    equipo = cliente.get("/users", headers=con_token(token_dueno)).json()["data"]
    assert [persona["active"] for persona in equipo] == [True] * 6
    assert entrar(cliente, "mecanico5@sancristobal.cl", clave=CLAVE_DEL_MECANICO)
    assert _contratar(cliente, token_dueno, 99).status_code == 409


def test_la_puerta_de_respaldo_respeta_el_tope(cliente, token_admin):
    """La regla es del taller, no de quien pregunta. Si Solve necesita pasarse, sube el plan."""
    taller_id, token_dueno = _taller_con_dueno_adentro(cliente, token_admin)
    _llenar_el_cupo(cliente, token_dueno)

    respuesta = cliente.post(
        f"/admin/workshops/{taller_id}/users",
        json={
            "name": "Uno de mas",
            "email": "unodemas@sancristobal.cl",
            "password": CLAVE_DEL_MECANICO,
        },
        headers=con_token(token_admin),
    )

    assert respuesta.status_code == 409, respuesta.text


def test_el_tope_no_cierra_la_puerta_de_emergencia(cliente, token_admin):
    """Devolverle un dueno al taller que perdio al suyo no puede depender del plan.

    El tope es de mecanicos: el dueno nunca ocupo cupo, y esta es la unica puerta que
    queda cuando adentro no hay nadie que pueda administrar.
    """
    taller_id, token_dueno = _taller_con_dueno_adentro(cliente, token_admin)
    _llenar_el_cupo(cliente, token_dueno)

    respuesta = cliente.post(
        f"/admin/workshops/{taller_id}/users",
        json={
            "name": "Dueno de repuesto",
            "email": "dueno2@sancristobal.cl",
            "password": CLAVE_DEL_MECANICO,
            "role": "owner",
        },
        headers=con_token(token_admin),
    )

    assert respuesta.status_code == 201, respuesta.text

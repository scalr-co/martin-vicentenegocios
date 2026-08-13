"""Suspender un taller hasta una fecha, y que vuelva solo.

Hasta aca la suspension era un interruptor: el taller quedaba fuera hasta que alguien se
acordara de reactivarlo. El panel, en cambio, ofrece "suspender hasta el 1 de septiembre",
que es lo que se necesita cuando un taller se atrasa con el pago y se acuerda una fecha.

La regla vive en el modelo -`puede_entrar`- y no en cada consulta, porque la contesta
tanto la puerta de entrada como la ficha que muestra el panel: si estuviera escrita dos
veces, un dia una diria que el taller entra y la otra lo mostraria suspendido.
"""

from datetime import timedelta

from sqlalchemy import select

from app.models import ACCION_TALLER_SUSPENDIDO, AdminAudit, Workshop
from app.models.base import ahora
from tests.conftest import con_token, entrar
from tests.test_admin import alta_de_taller
from tests.test_admin import clave_de_admin_configurada  # noqa: F401  (fixture autouse)
from tests.test_admin import token_admin  # noqa: F401  (fixture)

def _en_dos_semanas() -> str:
    """Una fecha futura calculada, no escrita: una constante se vence sola algun dia."""
    return (ahora() + timedelta(days=14)).isoformat()


def _mirarse(cliente, token):
    """El pedido mas barato que pasa por la puerta: sirve para saber si lo dejan entrar."""
    return cliente.get("/auth/me", headers=con_token(token))


def test_un_taller_suspendido_sin_fecha_deja_a_su_gente_afuera(cliente, sesion, taller, dueno):
    token = entrar(cliente, dueno.email)

    taller.active = False
    sesion.commit()

    assert _mirarse(cliente, token).status_code == 401


def test_con_la_fecha_todavia_por_delante_sigue_afuera(cliente, sesion, taller, dueno):
    token = entrar(cliente, dueno.email)

    taller.active = False
    taller.suspended_until = ahora() + timedelta(days=1)
    sesion.commit()

    assert _mirarse(cliente, token).status_code == 401


def test_cuando_se_cumple_la_fecha_el_taller_vuelve_solo(cliente, sesion, taller, dueno):
    """Y con el mismo token de antes: la suspension no cierra sesiones, corta el paso.

    Que vuelva sin que nadie lo toque es el punto de la fecha. Si hubiera que reactivarlo
    a mano, es el interruptor de siempre con una fecha escrita al lado.
    """
    token = entrar(cliente, dueno.email)

    taller.active = False
    taller.suspended_until = ahora() - timedelta(minutes=1)
    sesion.commit()

    assert _mirarse(cliente, token).status_code == 200


def test_un_taller_dado_de_baja_no_revive_por_una_fecha_vencida(cliente, sesion, taller, dueno):
    """`dar_de_baja` tambien deja `active` en falso, asi que sin esta guarda una fecha
    vieja arrastrada le abriria la puerta a un taller que ya se fue."""
    token = entrar(cliente, dueno.email)

    taller.active = False
    taller.suspended_until = ahora() - timedelta(days=30)
    taller.deleted_at = ahora()
    sesion.commit()

    assert _mirarse(cliente, token).status_code == 401


def test_la_fecha_que_vuelve_de_la_base_sin_huso_no_rompe_la_comparacion(sesion, taller):
    """SQLite devuelve las fechas sin huso aunque la columna sea DateTime(timezone=True).

    Comparada a secas contra un `datetime` con huso, Python levanta TypeError y la puerta
    responde 500 a todo el taller. Por eso `puede_entrar` normaliza antes de comparar.
    """
    taller.active = False
    taller.suspended_until = ahora() + timedelta(days=1)
    sesion.commit()
    # Vuelve a leer de la base, como haria el pedido siguiente.
    sesion.expire(taller)

    assert taller.suspended_until.tzinfo is None
    assert not taller.puede_entrar(ahora())


def test_el_estado_dice_en_cual_de_las_tres_situaciones_esta(sesion, taller):
    momento = ahora()
    assert taller.estado(momento) == "active"

    taller.active = False
    taller.suspended_until = momento + timedelta(days=1)
    assert taller.estado(momento) == "suspended"

    taller.suspended_until = momento - timedelta(days=1)
    assert taller.estado(momento) == "active"

    taller.deleted_at = momento
    assert taller.estado(momento) == "deleted"


# --- Como se suspende y como se lee, desde el panel ---------------------------------


def _suspender(cliente, token_admin, taller_id, **cuerpo):
    return cliente.patch(
        f"/admin/workshops/{taller_id}", json=cuerpo, headers=con_token(token_admin)
    )


def _taller_nuevo(cliente, token_admin) -> str:
    respuesta = alta_de_taller(cliente, token_admin)
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["data"]["workshop"]["id"]


def test_el_panel_suspende_hasta_una_fecha(cliente, token_admin):
    taller_id = _taller_nuevo(cliente, token_admin)
    hasta = _en_dos_semanas()

    respuesta = _suspender(cliente, token_admin, taller_id, active=False, suspendedUntil=hasta)

    assert respuesta.status_code == 200, respuesta.text
    taller = respuesta.json()["data"]
    assert taller["status"] == "suspended"
    assert taller["active"] is False
    assert taller["suspendIndefinite"] is False
    assert taller["suspendedUntil"] is not None


def test_suspender_sin_fecha_sigue_siendo_hasta_que_alguien_lo_reactive(cliente, token_admin):
    taller_id = _taller_nuevo(cliente, token_admin)

    respuesta = _suspender(cliente, token_admin, taller_id, active=False)

    taller = respuesta.json()["data"]
    assert taller["status"] == "suspended"
    assert taller["suspendIndefinite"] is True
    assert taller["suspendedUntil"] is None


def test_la_fecha_sola_no_significa_nada(cliente, token_admin):
    """Sin `active: false` al lado no se sabe que se esta pidiendo: mejor rechazarlo que
    inventar un estado a medias."""
    taller_id = _taller_nuevo(cliente, token_admin)

    sola = _suspender(cliente, token_admin, taller_id, suspendedUntil=_en_dos_semanas())
    contradictoria = _suspender(
        cliente, token_admin, taller_id, active=True, suspendedUntil=_en_dos_semanas()
    )

    assert sola.status_code == 422
    assert contradictoria.status_code == 422


def test_una_fecha_que_ya_paso_no_suspende_nada(cliente, token_admin):
    """Suspender hasta ayer es no suspender: el taller entraria en el pedido siguiente."""
    taller_id = _taller_nuevo(cliente, token_admin)
    ayer = (ahora() - timedelta(days=1)).isoformat()

    respuesta = _suspender(cliente, token_admin, taller_id, active=False, suspendedUntil=ayer)

    assert respuesta.status_code == 422


def test_reactivar_borra_la_fecha(cliente, token_admin, sesion):
    """Si quedara escrita, el taller volveria con una suspension agendada que nadie recuerda."""
    taller_id = _taller_nuevo(cliente, token_admin)
    _suspender(cliente, token_admin, taller_id, active=False, suspendedUntil=_en_dos_semanas())

    respuesta = _suspender(cliente, token_admin, taller_id, active=True)

    assert respuesta.json()["data"]["status"] == "active"
    assert respuesta.json()["data"]["suspendedUntil"] is None
    assert sesion.get(Workshop, taller_id).suspended_until is None


def test_el_taller_que_cumplio_su_fecha_se_lista_activo_sin_que_nadie_lo_toque(
    cliente, token_admin, sesion
):
    taller_id = _taller_nuevo(cliente, token_admin)
    _suspender(cliente, token_admin, taller_id, active=False, suspendedUntil=_en_dos_semanas())

    # Pasa el tiempo. Nadie entra al panel a reactivarlo.
    sesion.get(Workshop, taller_id).suspended_until = ahora() - timedelta(minutes=1)
    sesion.commit()

    lista = cliente.get("/admin/workshops", headers=con_token(token_admin)).json()["data"]
    ficha = cliente.get(
        f"/admin/workshops/{taller_id}", headers=con_token(token_admin)
    ).json()["data"]

    assert [taller["status"] for taller in lista if taller["id"] == taller_id] == ["active"]
    assert ficha["status"] == "active"
    assert ficha["active"] is True


def test_el_rastro_dice_hasta_cuando(cliente, token_admin, sesion):
    """Es lo que se lee cuando el taller llama preguntando por que no puede trabajar."""
    taller_id = _taller_nuevo(cliente, token_admin)

    _suspender(cliente, token_admin, taller_id, active=False, suspendedUntil=_en_dos_semanas())

    anotado = sesion.scalar(
        select(AdminAudit).where(
            AdminAudit.action == ACCION_TALLER_SUSPENDIDO,
            AdminAudit.workshop_id == taller_id,
        )
    )
    assert anotado is not None
    assert "hasta" in anotado.detail


def test_el_dueno_ve_su_taller_suspendido_al_entrar(cliente, token_admin, sesion, taller, dueno):
    """El login del taller trae el mismo estado que ve el panel, y no una version aparte."""
    taller.active = False
    taller.suspended_until = ahora() - timedelta(minutes=1)
    sesion.commit()

    respuesta = cliente.post(
        "/auth/login", json={"email": dueno.email, "password": "clave-de-prueba"}
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["data"]["workshop"]["status"] == "active"

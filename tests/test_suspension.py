"""Suspender un taller hasta una fecha, y que vuelva solo.

Hasta aca la suspension era un interruptor: el taller quedaba fuera hasta que alguien se
acordara de reactivarlo. El panel, en cambio, ofrece "suspender hasta el 1 de septiembre",
que es lo que se necesita cuando un taller se atrasa con el pago y se acuerda una fecha.

La regla vive en el modelo -`puede_entrar`- y no en cada consulta, porque la contesta
tanto la puerta de entrada como la ficha que muestra el panel: si estuviera escrita dos
veces, un dia una diria que el taller entra y la otra lo mostraria suspendido.
"""

from datetime import timedelta

from app.models.base import ahora
from tests.conftest import con_token, entrar


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

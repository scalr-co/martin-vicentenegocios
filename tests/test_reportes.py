"""El resumen semanal del taller: la ventaja que se cobra en el plan Plus.

Contesta la pregunta que un dueno de taller no puede contestar, porque esta debajo de un
auto: como le fue esta semana. Cuantos autos entraron, cuantos salieron, cuantos estan
esperando una respuesta suya y cuales llevan dias sin moverse.

El contrato de esta respuesta lo escribio el frontend antes que el backend
(`frontend/src/lib/plus-reports.ts`), asi que los nombres de los campos se respetan tal
cual: es el servidor el que calza con la pantalla, no al reves.
"""

from datetime import timedelta

from sqlalchemy import select

from app.models import ESTADO_CERRADO as ESTADO_ENTREGADO
from app.models import Order, OrderEvent
from app.models.base import ahora
from app.models.workshop import PLAN_PLUS
from tests.conftest import con_token, crear_cliente_api, crear_vehiculo_api, entrar
from tests.test_admin import alta_de_taller
from tests.test_admin import clave_de_admin_configurada  # noqa: F401  (fixture autouse)
from tests.test_admin import token_admin  # noqa: F401  (fixture)

CLAVE_DEL_DUENO = "una-clave-larga-de-verdad"


def _taller_plus(cliente, token_admin, **cambios) -> str:
    """Un taller del plan que paga el resumen, con su dueno adentro."""
    respuesta = alta_de_taller(cliente, token_admin, plan=PLAN_PLUS, **cambios)
    assert respuesta.status_code == 201, respuesta.text
    correo = cambios.get("email", "marcela@sancristobal.cl")
    return entrar(cliente, correo, clave=CLAVE_DEL_DUENO)


_telefonos = iter(range(11111111, 99999999))


def _orden(cliente, token, titulo: str, patente: str, estado: str | None = None) -> str:
    """Un auto que entra al taller, y opcionalmente avanza hasta un estado."""
    cliente_id = crear_cliente_api(cliente, token, telefono=f"569{next(_telefonos)}")
    vehiculo_id = crear_vehiculo_api(cliente, token, cliente_id, patente=patente)
    respuesta = cliente.post(
        "/orders",
        json={"clientId": cliente_id, "vehicleId": vehiculo_id, "title": titulo},
        headers=con_token(token),
    )
    assert respuesta.status_code == 201, respuesta.text
    orden_id = respuesta.json()["data"]["id"]

    if estado is not None:
        movida = cliente.post(
            f"/orders/{orden_id}/status", json={"status": estado}, headers=con_token(token)
        )
        assert movida.status_code == 200, movida.text
    return orden_id


def test_el_resumen_cuenta_lo_que_el_taller_tiene_entre_manos(cliente, token_admin):
    token = _taller_plus(cliente, token_admin)
    _orden(cliente, token, "Frenos", "AAAA11")
    _orden(cliente, token, "Presupuesto motor", "BBBB22", estado="esperando_aprobacion")
    _orden(cliente, token, "Falta el filtro", "CCCC33", estado="esperando_repuesto")
    _orden(cliente, token, "Terminado", "DDDD44", estado="listo")
    _orden(cliente, token, "Se lo llevo", "EEEE55", estado=ESTADO_ENTREGADO)

    respuesta = cliente.get("/reports/weekly", headers=con_token(token))

    assert respuesta.status_code == 200, respuesta.text
    resumen = respuesta.json()["data"]
    assert resumen["workshopName"] == "Taller San Cristobal"
    assert resumen["ordersOpen"] == 4  # las cinco menos la entregada
    assert resumen["ordersWaiting"] == 2  # aprobacion + repuesto: las que esperan a alguien
    assert resumen["ordersReady"] == 1  # lista, esperando que el cliente la venga a buscar
    assert resumen["ordersCreated"] == 5
    assert resumen["ordersDelivered"] == 1


def test_las_de_la_semana_pasada_no_se_cuentan_como_de_esta(cliente, token_admin, sesion):
    """La ventana son los ultimos 7 dias. Sin eso, el resumen del lunes 20 mostraria el
    trabajo de todo el ano y no diria nada sobre la semana."""
    token = _taller_plus(cliente, token_admin)
    _orden(cliente, token, "De hace un mes", "AAAA11", estado=ESTADO_ENTREGADO)
    _orden(cliente, token, "De esta semana", "BBBB22", estado=ESTADO_ENTREGADO)

    vieja = sesion.scalar(select(Order).where(Order.title == "De hace un mes"))
    hace_un_mes = ahora() - timedelta(days=30)
    vieja.created_at = hace_un_mes
    for evento in sesion.scalars(select(OrderEvent).where(OrderEvent.order_id == vieja.id)):
        evento.created_at = hace_un_mes
    sesion.commit()

    resumen = cliente.get("/reports/weekly", headers=con_token(token)).json()["data"]

    assert resumen["ordersCreated"] == 1
    assert resumen["ordersDelivered"] == 1


def test_las_ordenes_abiertas_salen_de_la_mas_vieja_a_la_mas_nueva(cliente, token_admin):
    """La que lleva mas tiempo sin salir es la que hay que mirar primero."""
    token = _taller_plus(cliente, token_admin)
    _orden(cliente, token, "La primera que entro", "AAAA11")
    _orden(cliente, token, "La segunda", "BBBB22")
    _orden(cliente, token, "Ya se la llevaron", "CCCC33", estado=ESTADO_ENTREGADO)

    resumen = cliente.get("/reports/weekly", headers=con_token(token)).json()["data"]

    assert [orden["title"] for orden in resumen["openOrders"]] == [
        "La primera que entro",
        "La segunda",
    ]
    assert resumen["openOrders"][0]["status"] == "recibido"
    assert "id" in resumen["openOrders"][0]


def test_el_desglose_por_estado_solo_cuenta_lo_que_esta_adentro(cliente, token_admin):
    """Las entregadas no van: el desglose responde "que tengo hoy", no "que hice alguna vez"."""
    token = _taller_plus(cliente, token_admin)
    _orden(cliente, token, "Una", "AAAA11")
    _orden(cliente, token, "Otra", "BBBB22")
    _orden(cliente, token, "Entregada", "CCCC33", estado=ESTADO_ENTREGADO)

    resumen = cliente.get("/reports/weekly", headers=con_token(token)).json()["data"]

    por_estado = {fila["status"]: fila["count"] for fila in resumen["byStatus"]}
    assert por_estado == {"recibido": 2}


def test_el_taller_de_al_lado_no_aparece_en_el_resumen(cliente, token_admin):
    """La regla de siempre: todo filtra por el taller del token."""
    token = _taller_plus(cliente, token_admin)
    _orden(cliente, token, "Mia", "AAAA11")

    token_vecino = _taller_plus(
        cliente, token_admin, email="otro@vecino.cl", workshopName="Taller Vecino"
    )
    _orden(cliente, token_vecino, "Suya", "BBBB22")
    _orden(cliente, token_vecino, "Suya tambien", "CCCC33")

    resumen = cliente.get("/reports/weekly", headers=con_token(token)).json()["data"]

    assert resumen["ordersOpen"] == 1
    assert [orden["title"] for orden in resumen["openOrders"]] == ["Mia"]


def test_el_plan_basico_no_tiene_resumen(cliente, token_admin):
    """La ventaja se cobra en el Plus. Esconder el boton no alcanza: el servidor tambien
    tiene que decir que no, o cualquiera lo pide a mano."""
    respuesta_alta = alta_de_taller(cliente, token_admin)
    assert respuesta_alta.status_code == 201
    token = entrar(cliente, "marcela@sancristobal.cl", clave=CLAVE_DEL_DUENO)

    respuesta = cliente.get("/reports/weekly", headers=con_token(token))

    assert respuesta.status_code == 403
    assert "Plus" in respuesta.json()["error"]["message"]


def test_sin_sesion_no_hay_resumen(cliente):
    assert cliente.get("/reports/weekly").status_code == 401

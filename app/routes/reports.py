"""El resumen semanal del taller, que es lo que se cobra en el plan Plus.

Contesta una pregunta que el dueno no puede contestar solo, porque la respuesta esta
repartida en cincuenta ordenes: como le fue esta semana. Cuantos autos entraron, cuantos
salieron, cuantos estan parados esperando que alguien conteste, y cuales llevan mas tiempo
sin moverse.

Se arma con lo que ya esta en la base. No hay tabla nueva ni proceso que corra de noche:
si se cayera este archivo entero, no se pierde un solo dato.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import ESTADO_CERRADO, Order, OrderEvent, User
from app.models.base import ahora
from app.models.order import ESTADO_ESPERANDO_APROBACION, ESTADO_ESPERANDO_REPUESTO, ESTADO_LISTO
from app.models.workshop import con_huso
from app.schemas.base import Respuesta
from app.schemas.reporte import ConteoPorEstado, OrdenEnResumen, ResumenSemanal
from app.security.dependencias import solo_plan_plus

router = APIRouter(prefix="/reports", tags=["reports"])

# Una semana hacia atras. El resumen se lee el lunes y habla de los ultimos siete dias, no
# del mes ni del ano: un numero que junta todo lo que paso no dice nada de esta semana.
VENTANA = timedelta(days=7)

# Los dos estados en que el taller esta detenido esperando a otro. No es lo mismo que estar
# trabajando: son autos parados, y es justo lo que se le escapa al dueno.
ESTADOS_EN_ESPERA = (ESTADO_ESPERANDO_APROBACION, ESTADO_ESPERANDO_REPUESTO)


@router.get("/weekly", response_model=Respuesta[ResumenSemanal])
def semanal(
    usuario: User = Depends(solo_plan_plus),
    sesion: Session = Depends(obtener_sesion),
):
    """Como le fue al taller en los ultimos siete dias.

    Las fechas se comparan **en Python y no en el WHERE**: SQLite devuelve las fechas sin
    huso aunque la columna sea DateTime(timezone=True), asi que una ventana escrita como
    condicion SQL funciona en produccion (Postgres) y miente en desarrollo. Es el mismo
    motivo por el que la ventana del panel de soporte tampoco esta en la consulta.
    """
    hasta = ahora()
    desde = hasta - VENTANA

    ordenes = sesion.scalars(
        select(Order)
        .where(Order.workshop_id == usuario.workshop_id, Order.deleted_at.is_(None))
        .order_by(Order.created_at)
    ).all()

    abiertas = [orden for orden in ordenes if orden.status != ESTADO_CERRADO]

    por_estado: dict[str, int] = {}
    for orden in abiertas:
        por_estado[orden.status] = por_estado.get(orden.status, 0) + 1

    # Se cuentan las entregas por su evento y no por `updated_at` de la orden: corregirle
    # el titulo a una orden entregada le mueve el `updated_at`, y esa orden aparaceria
    # entregada de nuevo esta semana.
    entregadas = sesion.execute(
        select(OrderEvent.order_id, OrderEvent.created_at)
        .join(Order, OrderEvent.order_id == Order.id)
        .where(
            Order.workshop_id == usuario.workshop_id,
            Order.deleted_at.is_(None),
            OrderEvent.to_status == ESTADO_CERRADO,
        )
    ).all()
    entregadas_en_la_ventana = {
        orden_id for orden_id, cuando in entregadas if con_huso(cuando) >= desde
    }

    resumen = ResumenSemanal(
        workshop_name=usuario.workshop.name,
        desde=desde,
        to=hasta,
        orders_open=len(abiertas),
        orders_waiting=sum(por_estado.get(estado, 0) for estado in ESTADOS_EN_ESPERA),
        orders_ready=por_estado.get(ESTADO_LISTO, 0),
        orders_created=sum(1 for orden in ordenes if con_huso(orden.created_at) >= desde),
        orders_delivered=len(entregadas_en_la_ventana),
        by_status=[
            ConteoPorEstado(status=estado, count=total)
            for estado, total in por_estado.items()
        ],
        # De la mas vieja a la mas nueva: la que lleva mas tiempo adentro es la que hay que
        # mirar primero, y es la que el dueno no tiene como detectar.
        open_orders=[
            OrdenEnResumen(id=orden.id, title=orden.title, status=orden.status)
            for orden in abiertas
        ],
    )

    return {"data": resumen.model_dump(by_alias=True, mode="json")}

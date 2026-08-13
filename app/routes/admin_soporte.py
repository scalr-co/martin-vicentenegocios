"""Mirar hacia adentro de un taller, para poder ayudarlo.

Es la otra mitad del panel de Solve. `admin.py` administra la cuenta del taller -la crea,
la corrige, la suspende-; esto de aca mira lo que el taller tiene entre manos, que es lo
que hace falta cuando llaman diciendo "no me llego el aviso al cliente".

Dos limites, a proposito:

- **Se mira, no se toca.** Aca solo hay GET. Para arreglarle algo a un taller estan las
  acciones de `admin.py`, que dejan su rastro. Si esto aceptara un POST, el registro
  dejaria de poder distinguir lo que hizo el taller de lo que hicimos nosotros.
- **Es una puerta aparte.** `/orders`, `/clients` y `/vehicles` siguen filtrando por el
  taller del token, sin excepcion. El taller que se mira aca sale de la URL, y la URL
  solo la abre el rol de plataforma.
"""

from datetime import UTC, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import (
    ACCION_TALLER_MIRADO,
    AVISO_LISTO_PARA_ENVIAR,
    ESTADOS,
    AdminAudit,
    Notification,
    Order,
    OrderEvent,
    User,
    Workshop,
)
from app.models.base import ahora
from app.routes.admin import taller_del_panel
from app.routes.orders import TOPE_DE_PAGINAS, TOPE_POR_PAGINA, filtrar_ordenes, salida_de_orden
from app.schemas.admin import (
    EventoSalida,
    FichaDeTaller,
    OrdenDeSoporte,
    SenalesDelTaller,
    TallerDetallado,
)
from app.schemas.base import Respuesta, RespuestaPaginada
from app.schemas.order import AvisoSalida, OrdenSalida
from app.security.dependencias import solo_admin_plataforma

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(solo_admin_plataforma)],
)


VENTANA_DE_VISITA = timedelta(minutes=30)


def _anotar_la_visita(sesion: Session, admin: User, taller: Workshop) -> None:
    """Deja escrito que este admin entro a mirar este taller.

    Se anota una vez por rato y no una por click: revisar un taller media hora dejaria
    veinte filas identicas, y el registro se vuelve ilegible justo cuando hay que leerlo.
    Lo que interesa contestar es "quien entro a mirar Marbella, y cuando", no cuantas
    veces recargo la pagina.

    La comparacion se hace en Python y no en el WHERE porque SQLite devuelve las fechas
    sin huso aunque la columna sea DateTime(timezone=True): comparar alla contra una
    fecha con huso funciona en Postgres y se rompe en los tests.
    """
    ultima = sesion.scalar(
        select(AdminAudit)
        .where(
            AdminAudit.action == ACCION_TALLER_MIRADO,
            AdminAudit.actor_user_id == admin.id,
            AdminAudit.workshop_id == taller.id,
        )
        .order_by(AdminAudit.created_at.desc())
        .limit(1)
    )
    if ultima is not None:
        cuando = ultima.created_at
        if cuando.tzinfo is None:
            cuando = cuando.replace(tzinfo=UTC)
        if ahora() - cuando < VENTANA_DE_VISITA:
            return

    sesion.add(
        AdminAudit(
            actor_user_id=admin.id,
            action=ACCION_TALLER_MIRADO,
            workshop_id=taller.id,
        )
    )
    sesion.commit()


def _senales(sesion: Session, taller: Workshop) -> SenalesDelTaller:
    """Como le esta yendo al taller, en cinco numeros."""
    return SenalesDelTaller(
        # Cuenta las archivadas igual que `GET /admin/workshops`. Si aca se contaran solo
        # las vigentes, la lista diria 57 y la ficha del mismo taller diria 54, y esa
        # diferencia se lee como una falla del panel.
        orders_total=sesion.scalar(
            select(func.count(Order.id)).where(Order.workshop_id == taller.id)
        ),
        orders_open=sesion.scalar(
            filtrar_ordenes(
                select(func.count()).select_from(Order), taller.id, True, None, None
            )
        ),
        # `updated_at` y no la bitacora: sube al crear la orden, al corregirla y al
        # moverla de estado. La bitacora solo tiene los cambios de estado, asi que un
        # taller que ingreso tres autos hoy y todavia no los diagnostica se veria muerto.
        last_activity_at=sesion.scalar(
            select(func.max(Order.updated_at)).where(Order.workshop_id == taller.id)
        ),
        notices_pending=sesion.scalar(
            select(func.count(Notification.id)).where(
                Notification.workshop_id == taller.id,
                Notification.status == AVISO_LISTO_PARA_ENVIAR,
            )
        ),
        users_active=sesion.scalar(
            select(func.count(User.id)).where(
                User.workshop_id == taller.id, User.active.is_(True)
            )
        ),
    )


@router.get("/workshops/{taller_id}", response_model=Respuesta[FichaDeTaller])
def ficha_del_taller(
    taller_id: str,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    """El taller y como le esta yendo, en una sola respuesta.

    Se abre antes de revisar orden por orden. Los dados de baja tambien se abren: cuando
    un taller se va, lo que uno quiere es entender por que.

    Es la unica ruta de este archivo que escribe, y lo que escribe es su propio rastro:
    para mirar cualquier cosa de un taller hay que pasar por aca primero, asi que con
    esta linea alcanza para saber quien entro.
    """
    taller = taller_del_panel(sesion, taller_id, incluir_dados_de_baja=True)
    _anotar_la_visita(sesion, admin, taller)

    ficha = TallerDetallado.desde(taller).model_dump(by_alias=True, mode="json")
    ficha["stats"] = _senales(sesion, taller).model_dump(by_alias=True, mode="json")

    return {"data": ficha}


@router.get(
    "/workshops/{taller_id}/orders", response_model=RespuestaPaginada[OrdenSalida]
)
def ordenes_del_taller(
    taller_id: str,
    abiertas: bool = Query(default=False, alias="open"),
    search: str | None = Query(default=None, max_length=120),
    estado: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1, le=TOPE_DE_PAGINAS),
    limit: int = Query(default=20, ge=1, le=TOPE_POR_PAGINA),
    sesion: Session = Depends(obtener_sesion),
):
    """Las ordenes del taller, con los mismos filtros que ve el taller en su panel.

    Mismos filtros a proposito: cuando el dueno dice "no me aparece la orden de la
    camioneta", hay que poder mirar exactamente lo que el esta mirando.
    """
    if estado is not None and estado not in ESTADOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"'{estado}' no es un estado de orden. Son: {', '.join(ESTADOS)}",
        )

    taller = taller_del_panel(sesion, taller_id, incluir_dados_de_baja=True)

    total = sesion.scalar(
        filtrar_ordenes(
            select(func.count()).select_from(Order), taller.id, abiertas, search, estado
        )
    )
    encontradas = sesion.scalars(
        filtrar_ordenes(select(Order), taller.id, abiertas, search, estado)
        .order_by(Order.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    return {
        "data": [salida_de_orden(orden) for orden in encontradas],
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.get(
    "/workshops/{taller_id}/orders/{orden_id}", response_model=Respuesta[OrdenDeSoporte]
)
def detalle_de_la_orden(
    taller_id: str,
    orden_id: str,
    sesion: Session = Depends(obtener_sesion),
):
    """La orden con su bitacora y todos sus avisos.

    Es la pantalla del post-mortem: quien la movio, cuando, y si el WhatsApp de cada
    cambio llego a salir o quedo esperando que alguien apretara enviar. El panel del
    taller muestra solo el ultimo aviso -es lo que necesita para abrir wa.me-, y con eso
    no se puede contestar "a mi cliente nunca le avisaron".
    """
    taller = taller_del_panel(sesion, taller_id, incluir_dados_de_baja=True)

    # Los dos ids tienen que calzar. Que la orden exista no basta: el taller sale de la
    # URL, asi que sin esto bastaria cambiar un id para leer la orden de otro.
    orden = sesion.scalar(
        select(Order).where(
            Order.id == orden_id,
            Order.workshop_id == taller.id,
            Order.deleted_at.is_(None),
        )
    )
    if orden is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada"
        )

    # LEFT JOIN y no join a secas: el evento sobrevive a la persona, y con un join normal
    # la linea del mecanico que ya no esta desapareceria justo del historial que se mira
    # para entender que paso.
    eventos = sesion.execute(
        select(OrderEvent, User.name)
        .outerjoin(User, OrderEvent.user_id == User.id)
        .where(OrderEvent.order_id == orden.id)
        .order_by(OrderEvent.created_at)
    ).all()

    avisos = sesion.scalars(
        select(Notification)
        .where(Notification.order_id == orden.id)
        .order_by(Notification.created_at)
    ).all()

    salida = salida_de_orden(orden)
    salida["events"] = [
        EventoSalida(
            id=evento.id,
            type=evento.type,
            from_status=evento.from_status,
            to_status=evento.to_status,
            user_name=nombre,
            created_at=evento.created_at,
        ).model_dump(by_alias=True, mode="json")
        for evento, nombre in eventos
    ]
    salida["notifications"] = [
        AvisoSalida.model_validate(aviso).model_dump(by_alias=True, mode="json")
        for aviso in avisos
    ]

    return {"data": salida}

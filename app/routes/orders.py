"""Ordenes de trabajo.

Dos caminos separados a proposito: `PATCH /orders/:id` corrige el texto de la ficha y no
toca el estado; `POST /orders/:id/status` mueve el estado y por eso deja registrado quien
lo movio y escribe el aviso para el cliente.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import (
    AVISO_LISTO_PARA_ENVIAR,
    ESTADO_CERRADO,
    ESTADO_INICIAL,
    TIPO_CAMBIO_DE_ESTADO,
    Client,
    Notification,
    Order,
    OrderEvent,
    User,
    Vehicle,
)
from app.schemas.order import AvisoSalida, CambioDeEstado, OrdenEdicion, OrdenEntrada, OrdenSalida
from app.security.dependencias import usuario_actual
from app.services.mensajes import mensaje_para

router = APIRouter(prefix="/orders", tags=["orders"])

TOPE_POR_PAGINA = 100


def salida_de_orden(orden: Order) -> dict:
    return OrdenSalida.model_validate(orden).model_dump(by_alias=True, mode="json")


def _no_encontrada(que: str = "Orden") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{que} no encontrada")


def _del_taller(sesion: Session, usuario: User, orden_id: str) -> Order:
    orden = sesion.scalar(
        select(Order).where(
            Order.id == orden_id,
            Order.workshop_id == usuario.workshop_id,
        )
    )
    if orden is None:
        raise _no_encontrada()
    return orden


def _cliente_y_vehiculo(
    sesion: Session, usuario: User, client_id: str, vehicle_id: str
) -> tuple[Client, Vehicle]:
    """Comprueba que ambos sean del taller y que el auto sea de ese cliente.

    Lo segundo importa tanto como lo primero: si el vehiculo fuera de otro cliente, el
    aviso de "ya esta listo" saldria al telefono equivocado.
    """
    cliente = sesion.scalar(
        select(Client).where(
            Client.id == client_id,
            Client.workshop_id == usuario.workshop_id,
        )
    )
    if cliente is None:
        raise _no_encontrada("Cliente")

    vehiculo = sesion.scalar(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.workshop_id == usuario.workshop_id,
        )
    )
    if vehiculo is None:
        raise _no_encontrada("Vehiculo")

    if vehiculo.client_id != cliente.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ese vehiculo no es de ese cliente",
        )

    return cliente, vehiculo


@router.get("")
def listar(
    abiertas: bool = Query(default=False, alias="open"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=TOPE_POR_PAGINA),
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    condiciones = [Order.workshop_id == usuario.workshop_id]
    if abiertas:
        # Lo que el taller tiene entre manos: todo lo que todavia no se entrego.
        condiciones.append(Order.status != ESTADO_CERRADO)

    total = sesion.scalar(select(func.count()).select_from(Order).where(*condiciones))
    encontradas = sesion.scalars(
        select(Order)
        .where(*condiciones)
        .order_by(Order.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    return {
        "data": [salida_de_orden(orden) for orden in encontradas],
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(
    datos: OrdenEntrada,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    cliente, vehiculo = _cliente_y_vehiculo(sesion, usuario, datos.client_id, datos.vehicle_id)

    orden = Order(
        workshop_id=usuario.workshop_id,
        client_id=cliente.id,
        vehicle_id=vehiculo.id,
        title=datos.title,
        description=datos.description,
        estimated_at=datos.estimated_at,
        status=datos.status or ESTADO_INICIAL,
    )
    sesion.add(orden)
    sesion.commit()

    return {"data": salida_de_orden(orden)}


@router.get("/{orden_id}")
def obtener(
    orden_id: str,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    return {"data": salida_de_orden(_del_taller(sesion, usuario, orden_id))}


@router.patch("/{orden_id}")
def editar(
    orden_id: str,
    datos: OrdenEdicion,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    orden = _del_taller(sesion, usuario, orden_id)

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(orden, campo, valor)
    sesion.commit()

    return {"data": salida_de_orden(orden)}


@router.post("/{orden_id}/status")
def mover_de_estado(
    orden_id: str,
    datos: CambioDeEstado,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    orden = _del_taller(sesion, usuario, orden_id)

    if orden.status == datos.status:
        # Repetir el estado le mandaria al cliente el mismo mensaje dos veces.
        return {"data": {"order": salida_de_orden(orden), "notification": None}}

    anterior = orden.status
    orden.status = datos.status

    sesion.add(
        OrderEvent(
            order_id=orden.id,
            user_id=usuario.id,
            type=TIPO_CAMBIO_DE_ESTADO,
            from_status=anterior,
            to_status=datos.status,
        )
    )

    texto = datos.message or mensaje_para(
        datos.status,
        nombre_cliente=orden.client.name,
        patente=orden.vehicle.plate,
        marca=orden.vehicle.brand,
        modelo=orden.vehicle.model,
        nombre_taller=usuario.workshop.name,
    )

    aviso = Notification(
        workshop_id=orden.workshop_id,
        order_id=orden.id,
        client_id=orden.client_id,
        to_phone=orden.client.phone,
        message=texto,
        status=AVISO_LISTO_PARA_ENVIAR,
        triggered_by_user_id=usuario.id,
    )
    sesion.add(aviso)
    sesion.commit()

    return {
        "data": {
            "order": salida_de_orden(orden),
            "notification": AvisoSalida.model_validate(aviso).model_dump(
                by_alias=True, mode="json"
            ),
        }
    }

"""Ordenes de trabajo.

Dos caminos separados a proposito: `PATCH /orders/:id` corrige el texto de la ficha y no
toca el estado; `POST /orders/:id/status` mueve el estado y por eso deja registrado quien
lo movio y escribe el aviso para el cliente.

`DELETE /orders/:id` no borra: archiva. La orden sale del tablero pero la fila se queda,
porque de ella cuelgan los avisos que ya salieron por WhatsApp.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import (
    AVISO_LISTO_PARA_ENVIAR,
    ESTADO_CERRADO,
    ESTADO_INICIAL,
    ESTADOS,
    TIPO_CAMBIO_DE_ESTADO,
    Client,
    Notification,
    Order,
    OrderEvent,
    User,
    Vehicle,
    es_retroceso,
)
from app.models.base import ahora
from app.schemas.order import AvisoSalida, CambioDeEstado, OrdenEdicion, OrdenEntrada, OrdenSalida
from app.security.dependencias import usuario_actual
from app.services.mensajes import mensaje_para

router = APIRouter(prefix="/orders", tags=["orders"])

TOPE_POR_PAGINA = 100

# Tope por arriba del numero de pagina. Sin el, un numero enorme desborda el motor de
# la base al calcular el salto y lo que sale es un 500.
TOPE_DE_PAGINAS = 100_000


def salida_de_orden(orden: Order) -> dict:
    return OrdenSalida.model_validate(orden).model_dump(by_alias=True, mode="json")


def _ultimo_aviso(sesion: Session, orden_id: str) -> dict | None:
    """El aviso mas reciente de la orden, o None si no se le ha dicho nada al cliente.

    Va solo en el detalle y no en el listado: el aviso viaja en la respuesta del cambio
    de estado, y sin esto el mecanico que recarga la pagina pierde el texto que tenia
    que mandar y el id para marcarlo como enviado.
    """
    aviso = sesion.scalar(
        select(Notification)
        .where(Notification.order_id == orden_id)
        .order_by(Notification.created_at.desc())
        .limit(1)
    )
    if aviso is None:
        return None
    return AvisoSalida.model_validate(aviso).model_dump(by_alias=True, mode="json")


# El genero de cada palabra, porque el mensaje se arma con una sola funcion. Sin esto
# salia "Cliente no encontrada" y "Vehiculo no encontrada".
FALTA = {
    "Orden": "Orden no encontrada",
    "Cliente": "Cliente no encontrado",
    "Vehiculo": "Vehiculo no encontrado",
}


def _no_encontrada(que: str = "Orden") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=FALTA[que])


def _del_taller(sesion: Session, usuario: User, orden_id: str) -> Order:
    orden = sesion.scalar(
        select(Order).where(
            Order.id == orden_id,
            Order.workshop_id == usuario.workshop_id,
            Order.deleted_at.is_(None),
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
            Client.deleted_at.is_(None),
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


def filtrar_ordenes(
    consulta, workshop_id: str, abiertas: bool, search: str | None, estado: str | None
):
    """Los mismos filtros para la lista y para el total.

    Si el total se contara sin filtrar, el paginador del frontend ofreceria paginas que
    estan vacias.

    Recibe el `workshop_id` suelto y no el usuario porque el panel de Solve la reusa para
    mirar un taller que no es el suyo. Quien decide de que taller se trata es cada ruta:
    aca es el del token, y en `/admin/workshops/:id/orders` es el de la URL, detras del
    rol de plataforma.
    """
    consulta = consulta.where(
        Order.workshop_id == workshop_id,
        Order.deleted_at.is_(None),
    )

    if abiertas:
        # Lo que el taller tiene entre manos: todo lo que todavia no se entrego.
        consulta = consulta.where(Order.status != ESTADO_CERRADO)

    if estado:
        consulta = consulta.where(Order.status == estado)

    if search and search.strip():
        # El mecanico busca por lo que tiene delante: la patente del auto o el cliente.
        patron = f"%{search.strip()}%"
        consulta = (
            consulta.join(Client, Order.client_id == Client.id)
            .join(Vehicle, Order.vehicle_id == Vehicle.id)
            .where(or_(Vehicle.plate.ilike(patron), Client.name.ilike(patron)))
        )

    return consulta


@router.get("")
def listar(
    abiertas: bool = Query(default=False, alias="open"),
    search: str | None = Query(default=None, max_length=120),
    estado: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1, le=TOPE_DE_PAGINAS),
    limit: int = Query(default=20, ge=1, le=TOPE_POR_PAGINA),
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    if estado is not None and estado not in ESTADOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"'{estado}' no es un estado de orden. Son: {', '.join(ESTADOS)}",
        )

    total = sesion.scalar(
        filtrar_ordenes(
            select(func.count()).select_from(Order),
            usuario.workshop_id,
            abiertas,
            search,
            estado,
        )
    )
    encontradas = sesion.scalars(
        filtrar_ordenes(select(Order), usuario.workshop_id, abiertas, search, estado)
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

    abierta = sesion.scalar(
        select(Order).where(
            Order.vehicle_id == vehiculo.id,
            Order.workshop_id == usuario.workshop_id,
            Order.status != ESTADO_CERRADO,
            Order.deleted_at.is_(None),
        )
    )
    if abierta is not None:
        # Un auto esta en el taller una vez a la vez. Dos ordenes abiertas del mismo
        # vehiculo son dos tableros para un solo trabajo, y el cliente recibe avisos
        # cruzados de las dos. El auto que vuelve en tres meses no cae aca: esa ya
        # esta entregada.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ese vehiculo ya tiene una orden abierta en el taller",
        )

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
    orden = _del_taller(sesion, usuario, orden_id)
    salida = salida_de_orden(orden)
    salida["latestNotification"] = _ultimo_aviso(sesion, orden.id)
    return {"data": salida}


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


@router.delete("/{orden_id}", status_code=status.HTTP_204_NO_CONTENT)
def archivar(
    orden_id: str,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    """Saca la orden del tablero. Es para la que se creo mal, no para la que se termino.

    La que se termino se cierra moviendola a entregado, que es lo que le avisa al cliente.
    """
    orden = _del_taller(sesion, usuario, orden_id)
    orden.deleted_at = ahora()
    sesion.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


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

    if es_retroceso(anterior, datos.status):
        # Corregir un dedazo no es avanzar el trabajo: la orden se mueve y el cambio
        # queda en el historial, pero al cliente no se le escribe. Si el mecanico si
        # quiere avisarle, vuelve a avanzar el estado.
        sesion.commit()
        return {"data": {"order": salida_de_orden(orden), "notification": None}}

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

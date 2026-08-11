"""Vehiculos del taller.

Mismo criterio que en clientes: todo se filtra por el taller del token, y lo que es de
otro taller responde 404. El cliente al que se cuelga el vehiculo tambien se comprueba,
porque si no, mandando un id ajeno se podria escribir dentro del taller del vecino.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import Client, Order, User, Vehicle
from app.schemas.order import OrdenSalida
from app.schemas.vehicle import VehiculoEdicion, VehiculoEntrada, VehiculoSalida
from app.security.dependencias import usuario_actual
from app.services.normalizacion import DatoInvalido, normalizar_patente

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

TOPE_POR_PAGINA = 100

# Tope por arriba del numero de pagina. Sin el, un numero enorme desborda el motor de
# la base al calcular el salto y lo que sale es un 500.
TOPE_DE_PAGINAS = 100_000


def _salida(vehiculo: Vehicle) -> dict:
    return VehiculoSalida.model_validate(vehiculo).model_dump(by_alias=True, mode="json")


def _no_encontrado(que: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{que} no encontrado")


def _del_taller(sesion: Session, usuario: User, vehiculo_id: str) -> Vehicle:
    vehiculo = sesion.scalar(
        select(Vehicle).where(
            Vehicle.id == vehiculo_id,
            Vehicle.workshop_id == usuario.workshop_id,
        )
    )
    if vehiculo is None:
        raise _no_encontrado("Vehiculo")
    return vehiculo


def _exigir_cliente_propio(sesion: Session, usuario: User, client_id: str) -> None:
    existe = sesion.scalar(
        select(Client.id).where(
            Client.id == client_id,
            Client.workshop_id == usuario.workshop_id,
            Client.deleted_at.is_(None),
        )
    )
    if existe is None:
        raise _no_encontrado("Cliente")


def _patente_ya_usada(
    sesion: Session,
    workshop_id: str,
    patente: str,
    excepto_id: str | None = None,
) -> bool:
    condiciones = [Vehicle.workshop_id == workshop_id, Vehicle.plate == patente]
    if excepto_id is not None:
        condiciones.append(Vehicle.id != excepto_id)
    return sesion.scalar(select(Vehicle.id).where(*condiciones)) is not None


def _patente_repetida() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Ya hay un vehiculo con esa patente en el taller",
    )


@router.get("")
def listar(
    client_id: str | None = Query(default=None, alias="clientId"),
    plate: str | None = Query(default=None),
    page: int = Query(default=1, ge=1, le=TOPE_DE_PAGINAS),
    limit: int = Query(default=20, ge=1, le=TOPE_POR_PAGINA),
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    """Buscar por `plate` es como se llega a un auto que ya estuvo aca.

    La patente es el unico dato que el mecanico tiene en la mano cuando el auto entra
    por la puerta, y un auto que vuelve es el caso normal de un taller, no la excepcion.

    Los autos de un cliente archivado no salen. Si salieran, buscar la patente llevaria a
    una ficha que el taller ya no ve y armar la orden fallaria sin explicar por que. Por
    id si se pueden seguir pidiendo: es como los muestra una orden vieja.
    """
    condiciones = [
        Vehicle.workshop_id == usuario.workshop_id,
        Vehicle.client_id.in_(select(Client.id).where(Client.deleted_at.is_(None))),
    ]
    if client_id:
        condiciones.append(Vehicle.client_id == client_id)
    if plate:
        # Se guarda normalizada: sin esto, "bbbb 22" no encontraria nunca a "BBBB22".
        try:
            condiciones.append(Vehicle.plate == normalizar_patente(plate))
        except DatoInvalido:
            # Una patente imposible no es un error: es que no hay ningun auto asi.
            condiciones.append(Vehicle.plate.is_(None))

    total = sesion.scalar(select(func.count()).select_from(Vehicle).where(*condiciones))
    encontrados = sesion.scalars(
        select(Vehicle)
        .where(*condiciones)
        .order_by(Vehicle.plate)
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    return {
        "data": [_salida(vehiculo) for vehiculo in encontrados],
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(
    datos: VehiculoEntrada,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    _exigir_cliente_propio(sesion, usuario, datos.client_id)

    if _patente_ya_usada(sesion, usuario.workshop_id, datos.plate):
        raise _patente_repetida()

    vehiculo = Vehicle(
        workshop_id=usuario.workshop_id,
        client_id=datos.client_id,
        plate=datos.plate,
        brand=datos.brand,
        model=datos.model,
    )
    sesion.add(vehiculo)
    sesion.commit()

    return {"data": _salida(vehiculo)}


@router.get("/{vehiculo_id}")
def obtener(
    vehiculo_id: str,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    return {"data": _salida(_del_taller(sesion, usuario, vehiculo_id))}


@router.get("/{vehiculo_id}/history")
def historial(
    vehiculo_id: str,
    page: int = Query(default=1, ge=1, le=TOPE_DE_PAGINAS),
    limit: int = Query(default=20, ge=1, le=TOPE_POR_PAGINA),
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    """Todo lo que se le ha hecho a este auto, de lo mas nuevo a lo mas viejo.

    Es la pregunta de siempre cuando el auto vuelve: que le hicimos la vez pasada.
    """
    vehiculo = _del_taller(sesion, usuario, vehiculo_id)
    condiciones = [
        Order.vehicle_id == vehiculo.id,
        Order.workshop_id == usuario.workshop_id,
        Order.deleted_at.is_(None),
    ]

    total = sesion.scalar(select(func.count()).select_from(Order).where(*condiciones))
    ordenes = sesion.scalars(
        select(Order)
        .where(*condiciones)
        .order_by(Order.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    return {
        "data": [
            OrdenSalida.model_validate(orden).model_dump(by_alias=True, mode="json")
            for orden in ordenes
        ],
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.patch("/{vehiculo_id}")
def editar(
    vehiculo_id: str,
    datos: VehiculoEdicion,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    vehiculo = _del_taller(sesion, usuario, vehiculo_id)
    cambios = datos.model_dump(exclude_unset=True)

    patente_nueva = cambios.get("plate")
    if patente_nueva and _patente_ya_usada(
        sesion, usuario.workshop_id, patente_nueva, excepto_id=vehiculo.id
    ):
        raise _patente_repetida()

    for campo, valor in cambios.items():
        setattr(vehiculo, campo, valor)
    sesion.commit()

    return {"data": _salida(vehiculo)}

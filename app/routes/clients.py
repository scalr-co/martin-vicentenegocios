"""Fichas de clientes del taller.

Toda consulta filtra por el taller del token. Un taller no puede ver, ni tocar, ni
enterarse de que existe un cliente de otro: por eso lo ajeno responde 404 y no 403.

Una ficha archivada -`deleted_at` con fecha- se comporta como si no existiera: no sale en
la lista y pedirla responde 404. La fila sigue ahi porque de ella cuelgan los vehiculos,
las ordenes y los avisos del cliente.
"""

import re

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import ESTADO_CERRADO, Client, Order, User
from app.models.base import ahora
from app.schemas.client import ClienteEdicion, ClienteEntrada, ClienteSalida
from app.security.dependencias import usuario_actual

router = APIRouter(prefix="/clients", tags=["clients"])

TOPE_POR_PAGINA = 100

# Tope por arriba del numero de pagina. Sin el, un numero enorme desborda el motor de
# la base al calcular el salto y lo que sale es un 500.
TOPE_DE_PAGINAS = 100_000


def _salida(cliente: Client) -> dict:
    return ClienteSalida.model_validate(cliente).model_dump(by_alias=True, mode="json")


def _no_encontrado() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")


def _del_taller(sesion: Session, usuario: User, cliente_id: str) -> Client:
    cliente = sesion.scalar(
        select(Client).where(
            Client.id == cliente_id,
            Client.workshop_id == usuario.workshop_id,
            Client.deleted_at.is_(None),
        )
    )
    if cliente is None:
        raise _no_encontrado()
    return cliente


def _ficha_con_ese_telefono(
    sesion: Session,
    workshop_id: str,
    telefono: str,
    excepto_id: str | None = None,
) -> Client | None:
    """La ficha que ya tiene ese telefono, archivada o no.

    Las archivadas cuentan aunque el taller no las vea: la base no deja dos fichas con el
    mismo telefono dentro del taller, asi que ignorarlas reventaria al guardar.
    """
    condiciones = [Client.workshop_id == workshop_id, Client.phone == telefono]
    if excepto_id is not None:
        condiciones.append(Client.id != excepto_id)
    return sesion.scalar(select(Client).where(*condiciones))


def _telefono_repetido(archivada: bool = False) -> HTTPException:
    detalle = (
        "Ese telefono es de una ficha archivada del taller"
        if archivada
        else "Ya hay un cliente con ese telefono en el taller"
    )
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detalle)


def _ordenes_abiertas(sesion: Session, cliente_id: str) -> int:
    return sesion.scalar(
        select(func.count())
        .select_from(Order)
        .where(
            Order.client_id == cliente_id,
            Order.status != ESTADO_CERRADO,
            Order.deleted_at.is_(None),
        )
    )


@router.get("")
def listar(
    page: int = Query(default=1, ge=1, le=TOPE_DE_PAGINAS),
    limit: int = Query(default=20, ge=1, le=TOPE_POR_PAGINA),
    search: str | None = Query(default=None, max_length=120),
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    condiciones = [Client.workshop_id == usuario.workshop_id, Client.deleted_at.is_(None)]

    if search and search.strip():
        # El mecanico busca por lo que recuerda: el nombre, los ultimos digitos o el rut.
        patron = f"%{search.strip()}%"
        # El rut se compara sin guion de los dos lados: lo copia y pega con puntos.
        solo_rut = re.sub(r"[^0-9kK]", "", search).upper()
        buscado = [Client.name.ilike(patron), Client.phone.ilike(patron)]
        if solo_rut:
            buscado.append(func.replace(Client.rut, "-", "").ilike(f"%{solo_rut}%"))
        condiciones.append(or_(*buscado))

    total = sesion.scalar(select(func.count()).select_from(Client).where(*condiciones))
    encontrados = sesion.scalars(
        select(Client)
        .where(*condiciones)
        .order_by(Client.name)
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    return {
        "data": [_salida(cliente) for cliente in encontrados],
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(
    datos: ClienteEntrada,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    """Dar de alta al cliente. Si su ficha estaba archivada, la revive en vez de duplicarla.

    Revivir no es un atajo: el telefono es unico dentro del taller, asi que sin esto
    archivar dejaria ese numero inservible para siempre. Y es lo que el taller espera del
    cliente que vuelve -llega con el historial de su auto, no de cero-.
    """
    repetida = _ficha_con_ese_telefono(sesion, usuario.workshop_id, datos.phone)
    if repetida is not None and repetida.deleted_at is None:
        raise _telefono_repetido()

    if repetida is not None:
        cliente = repetida
        cliente.deleted_at = None
        cliente.name = datos.name
        cliente.rut = datos.rut
        cliente.notes = datos.notes
    else:
        cliente = Client(
            workshop_id=usuario.workshop_id,
            name=datos.name,
            phone=datos.phone,
            rut=datos.rut,
            notes=datos.notes,
        )
        sesion.add(cliente)

    sesion.commit()

    return {"data": _salida(cliente)}


@router.get("/{cliente_id}")
def obtener(
    cliente_id: str,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    return {"data": _salida(_del_taller(sesion, usuario, cliente_id))}


@router.patch("/{cliente_id}")
def editar(
    cliente_id: str,
    datos: ClienteEdicion,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    cliente = _del_taller(sesion, usuario, cliente_id)
    cambios = datos.model_dump(exclude_unset=True)

    telefono_nuevo = cambios.get("phone")
    if telefono_nuevo:
        repetida = _ficha_con_ese_telefono(
            sesion, usuario.workshop_id, telefono_nuevo, excepto_id=cliente.id
        )
        if repetida is not None:
            raise _telefono_repetido(archivada=repetida.deleted_at is not None)

    for campo, valor in cambios.items():
        setattr(cliente, campo, valor)
    sesion.commit()

    return {"data": _salida(cliente)}


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def archivar(
    cliente_id: str,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    """Saca la ficha de circulacion sin borrar nada de lo que se le hizo a sus autos.

    Con una orden abierta no se deja: el auto esta en el taller ahora mismo, y archivar
    al dueno lo dejaria fuera de la lista con el trabajo a medias. Primero se cierra o se
    archiva la orden.
    """
    cliente = _del_taller(sesion, usuario, cliente_id)

    abiertas = _ordenes_abiertas(sesion, cliente.id)
    if abiertas:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El cliente tiene {abiertas} orden(es) abierta(s). "
                "Cierra o archiva esas ordenes antes de archivar la ficha."
            ),
        )

    cliente.deleted_at = ahora()
    sesion.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

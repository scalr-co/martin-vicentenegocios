"""Fichas de clientes del taller.

Toda consulta filtra por el taller del token. Un taller no puede ver, ni tocar, ni
enterarse de que existe un cliente de otro: por eso lo ajeno responde 404 y no 403.
"""

import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import Client, User
from app.schemas.client import ClienteEdicion, ClienteEntrada, ClienteSalida
from app.security.dependencias import usuario_actual

router = APIRouter(prefix="/clients", tags=["clients"])

TOPE_POR_PAGINA = 100


def _salida(cliente: Client) -> dict:
    return ClienteSalida.model_validate(cliente).model_dump(by_alias=True, mode="json")


def _no_encontrado() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")


def _del_taller(sesion: Session, usuario: User, cliente_id: str) -> Client:
    cliente = sesion.scalar(
        select(Client).where(
            Client.id == cliente_id,
            Client.workshop_id == usuario.workshop_id,
        )
    )
    if cliente is None:
        raise _no_encontrado()
    return cliente


def _telefono_ya_usado(
    sesion: Session,
    workshop_id: str,
    telefono: str,
    excepto_id: str | None = None,
) -> bool:
    condiciones = [Client.workshop_id == workshop_id, Client.phone == telefono]
    if excepto_id is not None:
        condiciones.append(Client.id != excepto_id)
    return sesion.scalar(select(Client.id).where(*condiciones)) is not None


@router.get("")
def listar(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=TOPE_POR_PAGINA),
    search: str | None = Query(default=None, max_length=120),
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    condiciones = [Client.workshop_id == usuario.workshop_id]

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
    if _telefono_ya_usado(sesion, usuario.workshop_id, datos.phone):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya hay un cliente con ese telefono en el taller",
        )

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
    if telefono_nuevo and _telefono_ya_usado(
        sesion, usuario.workshop_id, telefono_nuevo, excepto_id=cliente.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya hay un cliente con ese telefono en el taller",
        )

    for campo, valor in cambios.items():
        setattr(cliente, campo, valor)
    sesion.commit()

    return {"data": _salida(cliente)}

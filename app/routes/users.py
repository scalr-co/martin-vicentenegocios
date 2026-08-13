"""El equipo del taller, administrado por su dueno.

Solve no participa: un taller que contrata a alguien el lunes no puede depender de que le
contesten. Para cuando el dueno se pierde existe la puerta de respaldo en
/admin/workshops/{id}/users, que si es de Solve y queda anotada.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import ROL_MECANICO, User
from app.schemas.user import UsuarioEntrada, UsuarioSalida
from app.security.dependencias import solo_dueno
from app.security.passwords import hashear
from app.services.altas import correo_libre

router = APIRouter(prefix="/users", tags=["users"])


def _salida(usuario: User) -> dict:
    return UsuarioSalida.model_validate(usuario).model_dump(by_alias=True)


def _del_taller(sesion: Session, dueno: User, usuario_id: str) -> User:
    """La persona buscada, solo si es del mismo taller que quien pregunta.

    404 y no 403 a proposito: un 403 sobre alguien de otro taller confirmaria que ese id
    existe. Es el mismo criterio de clientes, vehiculos y ordenes.
    """
    usuario = sesion.scalar(
        select(User).where(User.id == usuario_id, User.workshop_id == dueno.workshop_id)
    )
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    return usuario


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(
    datos: UsuarioEntrada,
    dueno: User = Depends(solo_dueno),
    sesion: Session = Depends(obtener_sesion),
):
    """Da de alta a un mecanico del taller.

    El rol lo pone esta linea y no el cuerpo del pedido: si se pudiera elegir, cualquier
    dueno se clonaria y la guarda del ultimo dueno activo no protegeria nada.
    """
    usuario = User(
        workshop_id=dueno.workshop_id,
        name=datos.name,
        email=correo_libre(sesion, datos.email),
        password_hash=hashear(datos.password),
        role=ROL_MECANICO,
    )
    sesion.add(usuario)
    sesion.commit()

    return {"data": _salida(usuario)}


@router.get("")
def listar(
    dueno: User = Depends(solo_dueno),
    sesion: Session = Depends(obtener_sesion),
):
    """Todo el equipo, incluidos los desactivados.

    Los apagados se muestran apagados en vez de esconderse: son justo los que se van a
    reactivar, y su nombre sigue apareciendo en el historial de las ordenes que movieron.
    """
    equipo = sesion.scalars(
        select(User)
        .where(User.workshop_id == dueno.workshop_id)
        .order_by(User.created_at)
    ).all()

    return {"data": [_salida(usuario) for usuario in equipo]}

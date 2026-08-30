"""El equipo del taller, administrado por su dueno.

Solve no participa: un taller que contrata a alguien el lunes no puede depender de que le
contesten. Para cuando el dueno se pierde existe la puerta de respaldo en
/admin/workshops/{id}/users, que si es de Solve y queda anotada.
"""

import hashlib
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import ROL_MECANICO, User, WorkshopInvitation
from app.models.base import ahora
from app.schemas.admin import ClaveNueva
from app.schemas.base import Respuesta
from app.schemas.user import (
    InvitacionTallerEntrada,
    InvitacionTallerSalida,
    UsuarioEdicion,
    UsuarioEntrada,
    UsuarioSalida,
)
from app.security.dependencias import solo_dueno
from app.security.passwords import hashear
from app.services.altas import correo_libre
from app.services.planes import verificar_cupo

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


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=Respuesta[UsuarioSalida]
)
def crear(
    datos: UsuarioEntrada,
    dueno: User = Depends(solo_dueno),
    sesion: Session = Depends(obtener_sesion),
):
    """Da de alta a un mecanico del taller.

    El rol lo pone esta linea y no el cuerpo del pedido: si se pudiera elegir, cualquier
    dueno se clonaria y la guarda del ultimo dueno activo no protegeria nada.
    """
    verificar_cupo(sesion, dueno.workshop)

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


@router.post(
    "/invitations",
    status_code=status.HTTP_201_CREATED,
    response_model=Respuesta[InvitacionTallerSalida],
)
def crear_invitacion(
    datos: InvitacionTallerEntrada,
    dueno: User = Depends(solo_dueno),
    sesion: Session = Depends(obtener_sesion),
):
    """Prepara un traslado, sin mover ni tocar la clave de nadie todavia.

    El token es privado y solo sirve para la cuenta cuyo correo se invito. El dueno lo
    comparte por el canal que prefiera; la persona lo acepta estando identificada.
    """
    email = str(datos.email).strip().lower()
    existente = sesion.scalar(select(User).where(User.email == email))
    if existente is None or existente.role != ROL_MECANICO:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un mecanico con ese correo",
        )
    if existente.workshop_id == dueno.workshop_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ese mecanico ya pertenece a este taller",
        )

    token = secrets.token_urlsafe(32)
    invitacion = WorkshopInvitation(
        workshop_id=dueno.workshop_id,
        created_by_user_id=dueno.id,
        email=email,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        expires_at=ahora() + timedelta(days=7),
    )
    sesion.add(invitacion)
    sesion.commit()

    return {"data": {"token": token, "expires_at": invitacion.expires_at}}


@router.get("", response_model=Respuesta[list[UsuarioSalida]])
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


@router.patch("/{usuario_id}", response_model=Respuesta[UsuarioSalida])
def editar(
    usuario_id: str,
    datos: UsuarioEdicion,
    dueno: User = Depends(solo_dueno),
    sesion: Session = Depends(obtener_sesion),
):
    """Cambia el nombre o enciende y apaga a una persona del taller.

    Apagar no borra: la cuenta deja de entrar y el nombre sigue colgando de cada orden
    que esa persona movio. Por eso es un interruptor y no un DELETE.
    """
    objetivo = _del_taller(sesion, dueno, usuario_id)
    cambios = datos.model_dump(exclude_unset=True)

    # El unico candado que hace falta. Quien pide esto es un dueno activo, asi que
    # apagando a otro el taller nunca se queda sin ninguno; lo unico que si lo dejaria
    # sin administracion es que se apagara a si mismo.
    if cambios.get("active") is False and objetivo.id == dueno.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes desactivar tu propia cuenta",
        )

    # Encender a alguien ocupa un cupo igual que contratarlo. Sin esto el tope del plan
    # se salta con dos clicks: apagar a uno, contratar a otro y volver a encender al
    # primero.
    if (
        cambios.get("active") is True
        and not objetivo.active
        and objetivo.role == ROL_MECANICO
    ):
        verificar_cupo(sesion, dueno.workshop)

    for campo, valor in cambios.items():
        if valor is not None:
            setattr(objetivo, campo, valor)
    sesion.commit()

    return {"data": _salida(objetivo)}


@router.post("/{usuario_id}/password", response_model=Respuesta[UsuarioSalida])
def cambiar_clave(
    usuario_id: str,
    datos: ClaveNueva,
    dueno: User = Depends(solo_dueno),
    sesion: Session = Depends(obtener_sesion),
):
    """Para el mecanico que perdio su clave. La escribe el dueno y se la pasa.

    Sube la version de sesion: cambiar la clave tiene que cortar lo que ya estaba
    abierto, o quien tuviera el token de antes seguiria adentro con una clave muerta.
    """
    objetivo = _del_taller(sesion, dueno, usuario_id)

    objetivo.password_hash = hashear(datos.password)
    objetivo.token_version += 1
    sesion.commit()

    return {"data": _salida(objetivo)}

"""Dar de alta un taller con su dueno.

Vive aca y no dentro de una ruta porque se entra por dos puertas: `/auth/register` con la
clave del servidor -la de emergencia- y el panel de admin con la cuenta de cada uno. Si el
alta estuviera escrita en las dos, se irian separando: una validaria algo que la otra no.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ROL_DUENO, User, Workshop
from app.schemas.auth import AltaTallerEntrada
from app.security.passwords import hashear


def crear_taller_con_dueno(
    sesion: Session, datos: AltaTallerEntrada, creado_por: User | None = None
) -> tuple[Workshop, User]:
    """Deja el taller y su dueno listos para entrar. No hace commit: decide quien llama.

    `creado_por` queda anotado en el taller: es lo que permite saber quien dio de alta a
    quien. Va vacio cuando el alta entra por `/auth/register`, que no tiene una persona
    detras sino la clave del servidor.

    Levanta 409 si el correo ya existe. El correo es unico en todo el sistema, asi que
    sin este chequeo el alta reventaria a mitad de camino con el taller ya creado.
    """
    if sesion.scalar(select(User).where(User.email == datos.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo",
        )

    taller = Workshop(
        name=datos.workshop_name,
        phone=datos.workshop_phone,
        created_by_user_id=creado_por.id if creado_por else None,
    )
    sesion.add(taller)
    sesion.flush()

    dueno = User(
        workshop_id=taller.id,
        name=datos.owner_name,
        email=datos.email,
        password_hash=hashear(datos.password),
        role=ROL_DUENO,
    )
    sesion.add(dueno)
    return taller, dueno

"""De donde sale "quien esta pidiendo esto".

Toda ruta protegida depende de usuario_actual. El usuario se busca en la base de datos
cada vez: un token firmado no alcanza si la persona fue desactivada o su taller suspendido.
"""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import ROL_DUENO, User
from app.security.tokens import TokenInvalido, leer_token

PREFIJO = "Bearer "


def _no_autenticado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesion invalida o vencida",
    )


def usuario_actual(
    peticion: Request,
    sesion: Session = Depends(obtener_sesion),
) -> User:
    cabecera = peticion.headers.get("Authorization", "")
    if not cabecera.startswith(PREFIJO):
        raise _no_autenticado()

    try:
        datos = leer_token(cabecera.removeprefix(PREFIJO).strip())
    except TokenInvalido:
        raise _no_autenticado() from None

    usuario = sesion.get(User, datos.user_id)
    if usuario is None or not usuario.active or not usuario.workshop.active:
        raise _no_autenticado()

    return usuario


def solo_dueno(usuario: User = Depends(usuario_actual)) -> User:
    """Para lo que administra el taller: usuarios, configuracion, estados."""
    if usuario.role != ROL_DUENO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta accion es solo para el dueno del taller",
        )
    return usuario

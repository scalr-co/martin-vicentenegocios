"""De donde sale "quien esta pidiendo esto".

Toda ruta protegida depende de usuario_actual. El usuario se busca en la base de datos
cada vez: un token firmado no alcanza si la persona fue desactivada o su taller suspendido.
"""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import PLAN_PLUS, ROL_ADMIN_PLATAFORMA, ROL_DUENO, User
from app.models.base import ahora
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
    if usuario is None or not usuario.active or not usuario.workshop.puede_entrar(ahora()):
        raise _no_autenticado()

    # La sesion se puede cerrar: si la version subio despues de emitir este token
    # -alguien cerro sus sesiones, o le cambiaron la clave- el token deja de servir.
    if usuario.token_version != datos.token_version:
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


def solo_plan_plus(usuario: User = Depends(usuario_actual)) -> User:
    """Para las ventajas que se cobran aparte.

    Esconder el boton en la pantalla no alcanza: sin esta linea, cualquiera con una sesion
    pide la URL a mano y se lleva gratis lo que el taller de al lado esta pagando. Es el
    mismo criterio del tope de mecanicos.
    """
    if usuario.workshop.plan != PLAN_PLUS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta funcion viene en el plan Plus",
        )
    return usuario


def solo_admin_plataforma(usuario: User = Depends(usuario_actual)) -> User:
    """Para el panel de Solve: dar de alta talleres y corregirlos.

    Administrar el propio taller no es administrar la plataforma: un dueno recibe 403.
    """
    if usuario.role != ROL_ADMIN_PLATAFORMA:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta accion es solo para la administracion de la plataforma",
        )
    return usuario

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import User
from app.schemas.auth import (
    LoginEntrada,
    LoginSalida,
    SesionSalida,
    UserSalida,
    WorkshopSalida,
)
from app.security.dependencias import usuario_actual
from app.security.passwords import verificar
from app.security.tokens import crear_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _credenciales_invalidas() -> HTTPException:
    """Un unico mensaje para clave mala y correo inexistente.

    Si fueran distintos, probando correos se podria averiguar cuales estan registrados.
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Correo o contrasena incorrectos",
    )


@router.post("/login")
def login(datos: LoginEntrada, sesion: Session = Depends(obtener_sesion)):
    usuario = sesion.scalar(select(User).where(User.email == datos.email))

    if usuario is None or not verificar(datos.password, usuario.password_hash):
        raise _credenciales_invalidas()
    if not usuario.active or not usuario.workshop.active:
        raise _credenciales_invalidas()

    token = crear_token(
        user_id=usuario.id,
        workshop_id=usuario.workshop_id,
        role=usuario.role,
    )
    salida = LoginSalida(
        token=token,
        workshop=WorkshopSalida.model_validate(usuario.workshop),
        user=UserSalida.model_validate(usuario),
    )
    return {"data": salida.model_dump(by_alias=True)}


@router.get("/me")
def me(usuario: User = Depends(usuario_actual)):
    salida = SesionSalida(
        workshop=WorkshopSalida.model_validate(usuario.workshop),
        user=UserSalida.model_validate(usuario),
    )
    return {"data": salida.model_dump(by_alias=True)}

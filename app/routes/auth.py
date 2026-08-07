import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import obtener_sesion
from app.models import ROL_DUENO, User, Workshop
from app.schemas.auth import (
    AltaTallerEntrada,
    LoginEntrada,
    LoginSalida,
    SesionSalida,
    UserSalida,
    WorkshopSalida,
)
from app.security.passwords import hashear
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


def _exigir_clave_de_administracion(clave_recibida: str | None) -> None:
    """Compara en tiempo constante: una comparacion normal filtra la clave letra a letra."""
    esperada = settings.admin_api_key
    if not esperada or not secrets.compare_digest(clave_recibida or "", esperada):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operacion es solo para administracion",
        )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    datos: AltaTallerEntrada,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
    sesion: Session = Depends(obtener_sesion),
):
    _exigir_clave_de_administracion(x_admin_key)

    if sesion.scalar(select(User).where(User.email == datos.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo",
        )

    taller = Workshop(name=datos.workshop_name, phone=datos.workshop_phone)
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
    sesion.commit()

    salida = LoginSalida(
        token=crear_token(user_id=dueno.id, workshop_id=taller.id, role=dueno.role),
        workshop=WorkshopSalida.model_validate(taller),
        user=UserSalida.model_validate(dueno),
    )
    return {"data": salida.model_dump(by_alias=True)}


@router.get("/me")
def me(usuario: User = Depends(usuario_actual)):
    salida = SesionSalida(
        workshop=WorkshopSalida.model_validate(usuario.workshop),
        user=UserSalida.model_validate(usuario),
    )
    return {"data": salida.model_dump(by_alias=True)}

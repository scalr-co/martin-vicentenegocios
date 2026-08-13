from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import User
from app.models.base import ahora
from app.schemas.auth import (
    AltaTallerEntrada,
    LoginEntrada,
    LoginSalida,
    SesionSalida,
    UserSalida,
    WorkshopSalida,
)
from app.schemas.base import Respuesta
from app.security.admin import exigir_clave_de_administracion
from app.security.dependencias import usuario_actual
from app.security.intentos import demasiados_intentos, olvidar, registrar_fallo
from app.security.passwords import verificar
from app.security.tokens import crear_token
from app.services.altas import crear_taller_con_dueno

router = APIRouter(prefix="/auth", tags=["auth"])


def _credenciales_invalidas() -> HTTPException:
    """Un unico mensaje para clave mala y correo inexistente.

    Si fueran distintos, probando correos se podria averiguar cuales estan registrados.
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Correo o contrasena incorrectos",
    )


def _demasiados_intentos() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Demasiados intentos con esa cuenta. Espera unos minutos y vuelve a probar.",
    )


@router.post("/login", response_model=Respuesta[LoginSalida])
def login(
    datos: LoginEntrada,
    peticion: Request,
    sesion: Session = Depends(obtener_sesion),
):
    direccion = peticion.client.host if peticion.client else "desconocida"

    # El freno va antes de mirar la clave: si la correcta pasara igual, no frenaria nada.
    if demasiados_intentos(datos.email, direccion):
        raise _demasiados_intentos()

    usuario = sesion.scalar(select(User).where(User.email == datos.email))

    if usuario is None or not verificar(datos.password, usuario.password_hash):
        registrar_fallo(datos.email, direccion)
        raise _credenciales_invalidas()
    # La misma regla que la puerta de cada pedido: un taller suspendido con fecha vuelve
    # a entrar solo cuando esa fecha se cumple, y aca tambien.
    if not usuario.active or not usuario.workshop.puede_entrar(ahora()):
        registrar_fallo(datos.email, direccion)
        raise _credenciales_invalidas()

    olvidar(datos.email, direccion)

    token = crear_token(
        user_id=usuario.id,
        workshop_id=usuario.workshop_id,
        role=usuario.role,
        token_version=usuario.token_version,
    )
    salida = LoginSalida(
        token=token,
        workshop=WorkshopSalida.desde(usuario.workshop),
        user=UserSalida.model_validate(usuario),
    )
    return {"data": salida.model_dump(by_alias=True)}


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=Respuesta[LoginSalida],
    dependencies=[Depends(exigir_clave_de_administracion)],
)
def register(
    datos: AltaTallerEntrada,
    sesion: Session = Depends(obtener_sesion),
):
    """La puerta de emergencia. El dia a dia va por el panel de admin, con cuenta propia."""
    taller, dueno = crear_taller_con_dueno(sesion, datos)
    sesion.commit()

    salida = LoginSalida(
        token=crear_token(
            user_id=dueno.id,
            workshop_id=taller.id,
            role=dueno.role,
            token_version=dueno.token_version,
        ),
        workshop=WorkshopSalida.desde(taller),
        user=UserSalida.model_validate(dueno),
    )
    return {"data": salida.model_dump(by_alias=True)}


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def cerrar_todas_las_sesiones(
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    """Deja fuera a todos los tokens ya emitidos de esta persona.

    Es lo que se hace cuando a alguien le roban el celular con la sesion abierta. No
    desactiva la cuenta: puede volver a entrar con su clave enseguida.

    Un JWT no se puede borrar del aparato donde quedo, asi que lo que se mueve es la
    version de sesion: el token viejo trae la anterior y deja de calzar.
    """
    usuario.token_version += 1
    sesion.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=Respuesta[SesionSalida])
def me(usuario: User = Depends(usuario_actual)):
    salida = SesionSalida(
        workshop=WorkshopSalida.desde(usuario.workshop),
        user=UserSalida.model_validate(usuario),
    )
    return {"data": salida.model_dump(by_alias=True)}

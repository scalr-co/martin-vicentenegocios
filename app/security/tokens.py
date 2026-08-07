"""Tokens de sesion (JWT).

El token lleva adentro quien es el usuario, a que taller pertenece y su rol. Va firmado,
asi que el cliente no lo puede modificar: cambiarle una letra lo invalida.

El workshop_id viaja aca a proposito. Ningun endpoint lo recibe como parametro, de modo
que un taller no puede pedir datos de otro cambiando un numero en la URL.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings

ALGORITMO = "HS256"
DURACION_POR_DEFECTO = timedelta(hours=12)


class TokenInvalido(Exception):
    """El token esta alterado, vencido, firmado con otra clave o no es un token."""


@dataclass(frozen=True)
class DatosToken:
    user_id: str
    workshop_id: str
    role: str


def crear_token(
    user_id: str,
    workshop_id: str,
    role: str,
    duracion: timedelta | None = None,
) -> str:
    vencimiento = datetime.now(UTC) + (duracion if duracion is not None else DURACION_POR_DEFECTO)
    contenido = {
        "sub": user_id,
        "workshop_id": workshop_id,
        "role": role,
        "exp": vencimiento,
    }
    return jwt.encode(contenido, settings.jwt_secret, algorithm=ALGORITMO)


def leer_token(token: str) -> DatosToken:
    try:
        contenido = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITMO])
        return DatosToken(
            user_id=contenido["sub"],
            workshop_id=contenido["workshop_id"],
            role=contenido["role"],
        )
    except (jwt.PyJWTError, KeyError) as error:
        raise TokenInvalido(str(error)) from error

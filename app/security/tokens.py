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
    token_version: int


def crear_token(
    user_id: str,
    workshop_id: str,
    role: str,
    token_version: int,
    duracion: timedelta | None = None,
) -> str:
    """El token lleva la version de sesion con la que se emitio.

    Es lo que permite cerrar una sesion: al validar se compara contra la que tiene la
    persona en la base, y si no calzan el token no sirve. Sin esto, un token firmado
    vale sus 12 horas completas pase lo que pase.
    """
    vencimiento = datetime.now(UTC) + (duracion if duracion is not None else DURACION_POR_DEFECTO)
    contenido = {
        "sub": user_id,
        "workshop_id": workshop_id,
        "role": role,
        "tv": token_version,
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
            # Un token de antes de que existiera la version no trae "tv" y cae en el
            # KeyError de abajo: se invalida. Es un login mas, una sola vez.
            token_version=contenido["tv"],
        )
    except (jwt.PyJWTError, KeyError) as error:
        raise TokenInvalido(str(error)) from error

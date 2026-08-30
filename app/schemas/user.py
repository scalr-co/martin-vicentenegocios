from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.models import ROL_DUENO, ROL_MECANICO
from app.schemas.base import Esquema, Texto

LARGO_MINIMO_DE_CLAVE = 8


class UsuarioEntrada(Esquema):
    """Alta de una persona del taller. El rol no viaja en el cuerpo: lo pone la ruta."""

    name: Texto = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=LARGO_MINIMO_DE_CLAVE, max_length=200)


class UsuarioDeRespaldoEntrada(UsuarioEntrada):
    """El alta que hace Solve. Aca si viaja el rol: es la unica puerta que puede
    devolverle un dueno al taller que perdio al suyo."""

    role: str = Field(default=ROL_MECANICO)

    @field_validator("role")
    @classmethod
    def _rol_conocido(cls, valor: str) -> str:
        if valor not in (ROL_DUENO, ROL_MECANICO):
            raise ValueError("El rol tiene que ser owner o mechanic")
        return valor


class UsuarioEdicion(Esquema):
    """`active` en falso apaga a la persona sin borrarla: su nombre sigue colgando del
    historial de cada orden que movio."""

    name: Texto | None = Field(default=None, min_length=2, max_length=120)
    active: bool | None = None


class UsuarioSalida(Esquema):
    """Sin `password_hash`, por lo mismo de siempre: lo que no se expone no se filtra."""

    id: str
    name: str
    email: EmailStr
    role: str
    active: bool
    created_at: datetime


class InvitacionTallerEntrada(Esquema):
    """El correo de una cuenta existente que un taller quiere contratar."""

    email: EmailStr


class InvitacionTallerSalida(Esquema):
    """El enlace solo se muestra al dueno que la acaba de crear."""

    token: str
    expires_at: datetime


class AceptarInvitacionTallerEntrada(Esquema):
    token: str = Field(min_length=32, max_length=200)

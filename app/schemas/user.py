from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.base import Esquema, Texto

LARGO_MINIMO_DE_CLAVE = 8


class UsuarioEntrada(Esquema):
    """Alta de una persona del taller. El rol no viaja en el cuerpo: lo pone la ruta."""

    name: Texto = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=LARGO_MINIMO_DE_CLAVE, max_length=200)


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

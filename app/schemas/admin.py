from pydantic import EmailStr, Field

from app.schemas.base import Esquema

LARGO_MINIMO_DE_CLAVE = 8


class CuentaAdminEntrada(Esquema):
    """Una cuenta de Solve. No pertenece a ningun taller de verdad."""

    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=LARGO_MINIMO_DE_CLAVE, max_length=200)


class UsuarioAdminSalida(Esquema):
    id: str
    name: str
    email: str
    role: str


class TallerEdicion(Esquema):
    """Solo lo que se corrige a mano. El nombre sale en el WhatsApp que lee el cliente."""

    name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, min_length=8, max_length=20)


class ClaveNueva(Esquema):
    password: str = Field(min_length=LARGO_MINIMO_DE_CLAVE, max_length=200)

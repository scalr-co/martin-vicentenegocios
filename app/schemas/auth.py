from pydantic import EmailStr, Field

from app.schemas.base import Esquema


class LoginEntrada(Esquema):
    email: EmailStr
    password: str


class AltaTallerEntrada(Esquema):
    """Crea el taller y su usuario dueno de una sola vez."""

    workshop_name: str = Field(min_length=2, max_length=120)
    workshop_phone: str = Field(min_length=8, max_length=20)
    owner_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)


class WorkshopSalida(Esquema):
    id: str
    name: str
    phone: str
    whatsapp_mode: str
    active: bool


class UserSalida(Esquema):
    """Sin password_hash a proposito: lo que no se expone no se puede filtrar."""

    id: str
    name: str
    email: EmailStr
    role: str


class SesionSalida(Esquema):
    workshop: WorkshopSalida
    user: UserSalida


class LoginSalida(SesionSalida):
    token: str

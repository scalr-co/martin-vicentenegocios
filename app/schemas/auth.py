from pydantic import EmailStr

from app.schemas.base import Esquema


class LoginEntrada(Esquema):
    email: EmailStr
    password: str


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

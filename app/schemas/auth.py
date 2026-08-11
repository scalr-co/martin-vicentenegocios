from pydantic import EmailStr, Field, field_validator

from app.schemas.base import Esquema, Texto
from app.services.normalizacion import DatoInvalido, normalizar_telefono


class LoginEntrada(Esquema):
    email: EmailStr
    password: str


class AltaTallerEntrada(Esquema):
    """Crea el taller y su usuario dueno de una sola vez."""

    workshop_name: Texto = Field(min_length=2, max_length=120)
    workshop_phone: str = Field(min_length=8, max_length=20)
    owner_name: Texto = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("workshop_phone")
    @classmethod
    def _telefono(cls, valor: str) -> str:
        """El mismo formato que el telefono de un cliente.

        El del taller se muestra en el panel y es a donde llama el cliente que responde
        el aviso: guardarlo a medias tiene el mismo costo que guardar mal el del cliente.
        """
        try:
            return normalizar_telefono(valor)
        except DatoInvalido as error:
            raise ValueError(str(error)) from None


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

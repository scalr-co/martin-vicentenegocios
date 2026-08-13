from typing import Annotated

from pydantic import AfterValidator, EmailStr, Field, field_validator

from app.models.workshop import PLAN_BASICO, PLANES
from app.schemas.base import Esquema, Texto
from app.services.normalizacion import DatoInvalido, normalizar_telefono


def _plan_que_se_vende(valor: str) -> str:
    """Solo los planes de la landing. Uno inventado no lo entiende ni la facturacion."""
    if valor not in PLANES:
        raise ValueError(f"'{valor}' no es un plan. Son: {', '.join(PLANES)}")
    return valor


# Se escribe una sola vez y se usa en las dos puertas por las que llega un plan: el alta
# del taller y la edicion desde el panel.
Plan = Annotated[str, AfterValidator(_plan_que_se_vende)]


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

    # El plan mas chico es el default: nadie recibe plus sin que alguien lo decida.
    plan: Plan = PLAN_BASICO

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
    plan: str


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

from typing import Annotated

from pydantic import AfterValidator, EmailStr, Field, field_validator

from app.models.base import ahora
from app.models.workshop import ESTADO_SUSPENDIDO, PLAN_BASICO, PLANES, Workshop
from app.schemas.base import Esquema, FechaUTC, Texto
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


def campos_de_estado(taller: Workshop) -> dict:
    """Como esta el taller ahora mismo, calculado en un solo lugar.

    Los cuatro campos son la misma respuesta contada de cuatro formas, porque el panel
    lee unas y el taller lee otras. Se arman aca y no en cada ruta para que no puedan
    contradecirse.
    """
    momento = ahora()
    estado = taller.estado(momento)
    return {
        "active": taller.puede_entrar(momento),
        "status": estado,
        "suspended_until": taller.suspended_until,
        "suspend_indefinite": estado == ESTADO_SUSPENDIDO and taller.suspended_until is None,
    }


class WorkshopSalida(Esquema):
    """El taller como lo lee cualquiera que tenga sesion.

    `active` responde "puede entrar hoy" y no "que dice la columna": desde que la
    suspension puede tener fecha de termino, las dos cosas dejaron de ser lo mismo, y la
    que le sirve a quien lee es la primera. Un campo, un significado.
    """

    id: str
    name: str
    phone: str
    whatsapp_mode: str
    plan: str
    active: bool
    status: str
    suspended_until: FechaUTC | None
    suspend_indefinite: bool

    @classmethod
    def desde(cls, taller: Workshop, **extra) -> "WorkshopSalida":
        """Se arma a mano y no con `model_validate` porque cuatro de sus campos no son
        columnas: se calculan mirando la hora. `extra` es para los esquemas que agregan
        campos encima de este."""
        return cls(
            id=taller.id,
            name=taller.name,
            phone=taller.phone,
            whatsapp_mode=taller.whatsapp_mode,
            plan=taller.plan,
            **campos_de_estado(taller),
            **extra,
        )


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

from datetime import datetime

from pydantic import Field, computed_field, field_validator

from app.schemas.base import Esquema
from app.services.normalizacion import DatoInvalido, normalizar_patente


def _patente_de_una_sola_forma(valor: str) -> str:
    """Traduce el rechazo de normalizacion al lenguaje de Pydantic, que responde 422."""
    try:
        return normalizar_patente(valor)
    except DatoInvalido as error:
        raise ValueError(str(error)) from None


class VehiculoEntrada(Esquema):
    client_id: str
    plate: str
    brand: str | None = Field(default=None, max_length=60)
    model: str | None = Field(default=None, max_length=60)

    @field_validator("plate")
    @classmethod
    def _patente(cls, valor: str) -> str:
        return _patente_de_una_sola_forma(valor)


class VehiculoEdicion(Esquema):
    """Todo opcional: llega solo lo que se corrigio de la ficha."""

    plate: str | None = None
    brand: str | None = Field(default=None, max_length=60)
    model: str | None = Field(default=None, max_length=60)

    @field_validator("plate")
    @classmethod
    def _patente(cls, valor: str | None) -> str | None:
        return None if valor is None else _patente_de_una_sola_forma(valor)


class VehiculoSalida(Esquema):
    id: str
    client_id: str
    plate: str
    brand: str | None
    model: str | None
    created_at: datetime

    @computed_field(alias="vehicleOrItem")
    @property
    def vehicle_or_item(self) -> str:
        """El auto ya escrito para mostrar, armado aca y no en el frontend.

        Asi el texto que ve el cliente en el aviso de WhatsApp y el que ve el mecanico
        en pantalla salen del mismo lugar y no se van separando con el tiempo.
        """
        descripcion = " ".join(parte for parte in (self.brand, self.model) if parte)
        if not descripcion:
            return f"Patente {self.plate}"
        return f"{descripcion} · Patente {self.plate}"

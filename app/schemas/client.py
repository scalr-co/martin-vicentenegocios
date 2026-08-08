from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.base import Esquema
from app.services.normalizacion import DatoInvalido, normalizar_telefono


def _en_formato_de_wame(valor: str) -> str:
    """Traduce el rechazo de normalizacion al lenguaje de Pydantic, que responde 422."""
    try:
        return normalizar_telefono(valor)
    except DatoInvalido as error:
        raise ValueError(str(error)) from None


class ClienteEntrada(Esquema):
    name: str = Field(min_length=2, max_length=120)
    phone: str
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("phone")
    @classmethod
    def _telefono(cls, valor: str) -> str:
        return _en_formato_de_wame(valor)


class ClienteEdicion(Esquema):
    """Todo opcional: llega solo lo que el mecanico cambio en la ficha."""

    name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("phone")
    @classmethod
    def _telefono(cls, valor: str | None) -> str | None:
        return None if valor is None else _en_formato_de_wame(valor)


class ClienteSalida(Esquema):
    id: str
    name: str
    phone: str
    notes: str | None
    created_at: datetime

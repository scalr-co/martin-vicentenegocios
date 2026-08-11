from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.base import Esquema, FechaUTC, Texto, TextoOpcional
from app.services.normalizacion import DatoInvalido, normalizar_rut, normalizar_telefono


def _en_formato_de_wame(valor: str) -> str:
    """Traduce el rechazo de normalizacion al lenguaje de Pydantic, que responde 422."""
    try:
        return normalizar_telefono(valor)
    except DatoInvalido as error:
        raise ValueError(str(error)) from None


def _rut_guardable(valor: str | None) -> str | None:
    """El campo es opcional, asi que el formulario vacio llega como "" y vale None."""
    if valor is None or not valor.strip():
        return None
    try:
        return normalizar_rut(valor)
    except DatoInvalido as error:
        raise ValueError(str(error)) from None


class ClienteEntrada(Esquema):
    name: Texto = Field(min_length=2, max_length=120)
    phone: str
    rut: str | None = None
    notes: TextoOpcional = Field(default=None, max_length=1000)

    @field_validator("phone")
    @classmethod
    def _telefono(cls, valor: str) -> str:
        return _en_formato_de_wame(valor)

    @field_validator("rut")
    @classmethod
    def _rut(cls, valor: str | None) -> str | None:
        return _rut_guardable(valor)


class ClienteEdicion(Esquema):
    """Todo opcional: llega solo lo que el mecanico cambio en la ficha."""

    name: TextoOpcional = Field(default=None, min_length=2, max_length=120)
    phone: str | None = None
    rut: str | None = None
    notes: TextoOpcional = Field(default=None, max_length=1000)

    @field_validator("phone")
    @classmethod
    def _telefono(cls, valor: str | None) -> str | None:
        return None if valor is None else _en_formato_de_wame(valor)

    @field_validator("rut")
    @classmethod
    def _rut(cls, valor: str | None) -> str | None:
        return _rut_guardable(valor)


class ClienteSalida(Esquema):
    id: str
    name: str
    phone: str
    rut: str | None
    notes: str | None
    created_at: FechaUTC

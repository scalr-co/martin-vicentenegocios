from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, PlainSerializer
from pydantic.alias_generators import to_camel


def _siempre_en_utc(valor: datetime) -> str:
    """Toda fecha sale igual: en UTC y terminada en Z.

    La misma fecha salia con Z al crear y sin Z al releer, porque SQLite devuelve las
    fechas sin huso aunque la columna sea DateTime(timezone=True). Un frontend que lea
    la segunda como hora local se equivoca en las 3 o 4 horas que Chile esta detras.
    """
    en_utc = valor.replace(tzinfo=UTC) if valor.tzinfo is None else valor.astimezone(UTC)
    return en_utc.isoformat().replace("+00:00", "Z")


# Solo al serializar a JSON: en modo python la fecha se sigue entregando como datetime.
FechaUTC = Annotated[
    datetime, PlainSerializer(_siempre_en_utc, return_type=str, when_used="json")
]


def _sin_espacios_en_los_bordes(valor: object) -> object:
    """Corre antes que min_length, asi "   " mide 0 y no 3.

    Sin esto la validacion cuenta caracteres y no contenido: un nombre de tres espacios
    pasaba el minimo de dos, se guardaba, y el taller quedaba con una ficha que se ve
    vacia en la lista y no se puede buscar.
    """
    return valor.strip() if isinstance(valor, str) else valor


# Para los campos que escribe una persona a mano. El largo se sigue declarando con
# Field(min_length=...); lo que cambia es que se mide sobre el texto ya limpio.
Texto = Annotated[str, BeforeValidator(_sin_espacios_en_los_bordes)]
TextoOpcional = Annotated[str | None, BeforeValidator(_sin_espacios_en_los_bordes)]


class Esquema(BaseModel):
    """Padre de todos los esquemas de entrada y salida.

    Por dentro escribimos en espanol con guion bajo (whatsapp_mode) y hacia afuera
    sale en el formato que espera el frontend (whatsappMode).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

from datetime import date, datetime

from pydantic import Field, computed_field, field_validator

from app.models.order import ESTADOS
from app.schemas.base import Esquema, Texto, TextoOpcional
from app.services.presentacion import describir_vehiculo


def _estado_conocido(valor: str | None) -> str | None:
    if valor is not None and valor not in ESTADOS:
        raise ValueError(f"'{valor}' no es un estado de orden. Son: {', '.join(ESTADOS)}")
    return valor


class ClienteResumen(Esquema):
    id: str
    name: str
    phone: str


class VehiculoResumen(Esquema):
    id: str
    plate: str
    brand: str | None
    model: str | None


class OrdenEntrada(Esquema):
    client_id: str
    vehicle_id: str
    title: Texto = Field(min_length=2, max_length=160)
    description: TextoOpcional = None
    estimated_at: date | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def _estado(cls, valor: str | None) -> str | None:
        return _estado_conocido(valor)


class OrdenEdicion(Esquema):
    """Sin `status` a proposito: el estado se mueve por su propio endpoint.

    Cambiar de estado le escribe al cliente. Si se pudiera hacer desde aca, corregir una
    palabra del titulo podria terminar mandando un WhatsApp sin que nadie lo pidiera.
    """

    title: TextoOpcional = Field(default=None, min_length=2, max_length=160)
    description: TextoOpcional = None
    estimated_at: date | None = None


class OrdenSalida(Esquema):
    id: str
    title: str
    description: str | None
    status: str
    estimated_at: date | None
    created_at: datetime
    updated_at: datetime
    client: ClienteResumen
    vehicle: VehiculoResumen

    @computed_field(alias="vehicleOrItem")
    @property
    def vehicle_or_item(self) -> str:
        return describir_vehiculo(self.vehicle.plate, self.vehicle.brand, self.vehicle.model)


class CambioDeEstado(Esquema):
    status: str

    # Lo que el mecanico escribio en vez del borrador. Si no viene, se usa la plantilla.
    message: str | None = Field(default=None, max_length=1000)

    @field_validator("status")
    @classmethod
    def _estado(cls, valor: str) -> str:
        return _estado_conocido(valor)


class AvisoEnviado(Esquema):
    """Lo que el mecanico mando de verdad, si cambio el borrador antes de enviarlo.

    Viene vacio cuando mando el borrador tal cual: ese es el caso normal.
    """

    message: str | None = Field(default=None, max_length=1000)

    @field_validator("message")
    @classmethod
    def _con_algo_adentro(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip()
        if not limpio:
            raise ValueError("El aviso no puede ir en blanco")
        return limpio


class AvisoSalida(Esquema):
    """Lo que el frontend necesita para abrir wa.me sin pedir nada mas."""

    id: str
    to_phone: str
    message: str
    status: str
    created_at: datetime
    sent_at: datetime | None = None

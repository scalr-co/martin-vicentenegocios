"""Lo que el taller ve de si mismo.

El contrato de estos campos lo escribio antes el frontend, en
`frontend/src/lib/plus-reports.ts`. Se respetan sus nombres tal cual: la pantalla ya estaba
escrita, asi que el que calza es el servidor.
"""

from pydantic import Field

from app.schemas.base import Esquema, FechaUTC


class OrdenEnResumen(Esquema):
    """Lo minimo para reconocer una orden en una lista. El detalle se pide aparte."""

    id: str
    title: str
    status: str


class ConteoPorEstado(Esquema):
    status: str
    count: int


class ResumenSemanal(Esquema):
    """Como le fue al taller esta semana, en los numeros que un dueno mira.

    `orders_waiting` junta los dos estados en que el taller esta detenido esperando a
    alguien -que el cliente apruebe, o que llegue el repuesto-, que es justo lo que se le
    escapa al dueno: no son autos en los que se este trabajando, son autos parados.
    """

    workshop_name: str

    # `from` es palabra reservada en Python, y el frontend ya lo pide con ese nombre.
    desde: FechaUTC = Field(alias="from")
    to: FechaUTC

    orders_open: int
    orders_waiting: int
    orders_ready: int
    orders_created: int
    orders_delivered: int

    by_status: list[ConteoPorEstado]
    open_orders: list[OrdenEnResumen]

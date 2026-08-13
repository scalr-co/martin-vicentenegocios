from pydantic import EmailStr, Field

from app.schemas.auth import Plan
from app.schemas.base import Esquema, FechaUTC, Texto
from app.services.altas import LARGO_MINIMO_DE_CLAVE_ADMIN

LARGO_MINIMO_DE_CLAVE = 8


class CuentaAdminEntrada(Esquema):
    """Una cuenta de Solve. No pertenece a ningun taller de verdad."""

    name: Texto = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=LARGO_MINIMO_DE_CLAVE_ADMIN, max_length=200)


class CuentaAdminEdicion(Esquema):
    name: Texto | None = Field(default=None, min_length=2, max_length=120)
    active: bool | None = None


class UsuarioAdminSalida(Esquema):
    id: str
    name: str
    email: str
    role: str
    active: bool


class TallerEdicion(Esquema):
    """Solo lo que se corrige a mano. El nombre sale en el WhatsApp que lee el cliente.

    `active` en falso suspende el taller: nadie de ahi entra, y sus datos quedan enteros.
    """

    name: Texto | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, min_length=8, max_length=20)
    active: bool | None = None
    plan: Plan | None = None


class ClaveNueva(Esquema):
    password: str = Field(min_length=LARGO_MINIMO_DE_CLAVE, max_length=200)


class EventoSalida(Esquema):
    """Una linea de la bitacora de la orden, como se lee desde el panel de Solve.

    Va el nombre de la persona y no su id: quien mira desde afuera no tiene forma de
    saber a quien corresponde un uuid del taller de otro. Queda en null si la cuenta se
    borro, porque el evento sobrevive a la persona.
    """

    id: str
    type: str
    from_status: str | None
    to_status: str | None
    user_name: str | None
    created_at: FechaUTC


class SenalesDelTaller(Esquema):
    """Como le esta yendo al taller, en cinco numeros.

    Es lo que se mira antes de entrar a revisar orden por orden. `notices_pending` es la
    senal mas util de todas: un taller que mueve ordenes y deja los avisos sin enviar no
    esta usando el producto, esta peleando con el.
    """

    orders_total: int
    orders_open: int
    last_activity_at: FechaUTC | None
    notices_pending: int
    users_active: int


class TallerDetallado(Esquema):
    """El taller como lo ve el panel al abrir su ficha.

    Trae mas que `WorkshopSalida`: cuando entro y cuando se fue, que es lo que se mira al
    revisar un taller que dejo de estar. Las senales van aparte, en `stats`.
    """

    id: str
    name: str
    phone: str
    whatsapp_mode: str
    active: bool
    plan: str
    created_at: FechaUTC
    deleted_at: FechaUTC | None

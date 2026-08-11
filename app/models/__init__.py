"""Todas las tablas se importan aca para que SQLAlchemy las conozca al crear el esquema."""

from app.models.client import Client
from app.models.notification import (
    AVISO_ENVIADO,
    AVISO_FALLIDO,
    AVISO_LISTO_PARA_ENVIAR,
    AVISO_PENDIENTE,
    CANAL_WHATSAPP,
    Notification,
)
from app.models.order import (
    ESTADO_CERRADO,
    ESTADO_INICIAL,
    ESTADOS,
    Order,
    es_retroceso,
)
from app.models.order_event import TIPO_CAMBIO_DE_ESTADO, OrderEvent
from app.models.user import ROL_ADMIN_PLATAFORMA, ROL_DUENO, ROL_MECANICO, User
from app.models.vehicle import Vehicle
from app.models.workshop import MODO_API, MODO_LINK, Workshop

__all__ = [
    "ROL_ADMIN_PLATAFORMA",
    "ROL_DUENO",
    "ROL_MECANICO",
    "MODO_API",
    "MODO_LINK",
    "ESTADOS",
    "ESTADO_INICIAL",
    "ESTADO_CERRADO",
    "TIPO_CAMBIO_DE_ESTADO",
    "CANAL_WHATSAPP",
    "AVISO_PENDIENTE",
    "AVISO_LISTO_PARA_ENVIAR",
    "AVISO_ENVIADO",
    "AVISO_FALLIDO",
    "Client",
    "Notification",
    "Order",
    "OrderEvent",
    "User",
    "Vehicle",
    "Workshop",
    "es_retroceso",
]

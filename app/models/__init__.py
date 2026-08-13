"""Todas las tablas se importan aca para que SQLAlchemy las conozca al crear el esquema."""

from app.models.admin_audit import (
    ACCION_CLAVE_DEL_DUENO_CAMBIADA,
    ACCION_CUENTA_ADMIN_CREADA,
    ACCION_CUENTA_ADMIN_EDITADA,
    ACCION_TALLER_CREADO,
    ACCION_TALLER_DADO_DE_BAJA,
    ACCION_TALLER_EDITADO,
    ACCION_TALLER_MIRADO,
    ACCION_TALLER_REACTIVADO,
    ACCION_TALLER_RESTAURADO,
    ACCION_TALLER_SUSPENDIDO,
    ACCION_USUARIO_CREADO,
    AdminAudit,
)
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
from app.models.workshop import (
    MAX_MECANICOS_BASICO,
    MODO_API,
    MODO_LINK,
    PLAN_BASICO,
    PLAN_PLUS,
    PLANES,
    Workshop,
)

__all__ = [
    "ACCION_TALLER_CREADO",
    "ACCION_TALLER_EDITADO",
    "ACCION_TALLER_SUSPENDIDO",
    "ACCION_TALLER_REACTIVADO",
    "ACCION_TALLER_DADO_DE_BAJA",
    "ACCION_TALLER_RESTAURADO",
    "ACCION_TALLER_MIRADO",
    "ACCION_USUARIO_CREADO",
    "ACCION_CUENTA_ADMIN_CREADA",
    "ACCION_CUENTA_ADMIN_EDITADA",
    "ACCION_CLAVE_DEL_DUENO_CAMBIADA",
    "AdminAudit",
    "ROL_ADMIN_PLATAFORMA",
    "ROL_DUENO",
    "ROL_MECANICO",
    "MODO_API",
    "MODO_LINK",
    "PLAN_BASICO",
    "PLAN_PLUS",
    "PLANES",
    "MAX_MECANICOS_BASICO",
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

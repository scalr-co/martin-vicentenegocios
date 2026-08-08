from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import ahora, nuevo_id
from app.models.client import Client
from app.models.vehicle import Vehicle

ESTADO_RECIBIDO = "recibido"
ESTADO_EN_DIAGNOSTICO = "en_diagnostico"
ESTADO_ESPERANDO_APROBACION = "esperando_aprobacion"
ESTADO_EN_REPARACION = "en_reparacion"
ESTADO_ESPERANDO_REPUESTO = "esperando_repuesto"
ESTADO_LISTO = "listo"
ESTADO_ENTREGADO = "entregado"

# En el orden en que ocurren, que es el orden en que se muestran.
ESTADOS = (
    ESTADO_RECIBIDO,
    ESTADO_EN_DIAGNOSTICO,
    ESTADO_ESPERANDO_APROBACION,
    ESTADO_EN_REPARACION,
    ESTADO_ESPERANDO_REPUESTO,
    ESTADO_LISTO,
    ESTADO_ENTREGADO,
)

ESTADO_INICIAL = ESTADO_RECIBIDO

# Entregado es el unico estado que cierra la orden: deja de aparecer en el panel.
ESTADO_CERRADO = ESTADO_ENTREGADO


class Order(Base):
    """Un trabajo sobre un vehiculo. Su estado es lo que el cliente sigue por WhatsApp."""

    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=nuevo_id)
    workshop_id: Mapped[str] = mapped_column(ForeignKey("workshops.id"), index=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), index=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id"), index=True)

    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text, default=None)

    status: Mapped[str] = mapped_column(String(30), default=ESTADO_INICIAL, index=True)

    # Fecha sin hora: al cliente se le promete un dia, no un minuto.
    estimated_at: Mapped[date | None] = mapped_column(Date, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=ahora, onupdate=ahora
    )

    # Se traen juntos porque la orden nunca se muestra sin ellos.
    client: Mapped[Client] = relationship(lazy="joined")
    vehicle: Mapped[Vehicle] = relationship(lazy="joined")

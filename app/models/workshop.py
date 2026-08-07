from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import ahora, nuevo_id

MODO_LINK = "link"
MODO_API = "api"


class Workshop(Base):
    """Un taller. Es la unidad de aislamiento: todo lo demas le pertenece a uno."""

    __tablename__ = "workshops"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=nuevo_id)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))

    # "link": el frontend abre wa.me y el mecanico aprieta enviar.
    # "api": envio automatico por Meta. Reservado, todavia sin implementar.
    whatsapp_mode: Mapped[str] = mapped_column(String(10), default=MODO_LINK)

    timezone: Mapped[str] = mapped_column(String(60), default="America/Santiago")

    # Permite suspender un taller sin borrarle los datos.
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

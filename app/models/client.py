from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import ahora, nuevo_id


class Client(Base):
    """La persona que deja su vehiculo. Es a quien se le avisa por WhatsApp."""

    __tablename__ = "clients"

    # El mismo telefono puede estar en dos talleres distintos, pero no dos veces en el
    # mismo: dos fichas de la misma persona le parten el historial en dos.
    __table_args__ = (
        UniqueConstraint("workshop_id", "phone", name="uq_clients_taller_telefono"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=nuevo_id)
    workshop_id: Mapped[str] = mapped_column(ForeignKey("workshops.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))

    # Guardado solo con digitos: es lo que se le pega al link de wa.me.
    phone: Mapped[str] = mapped_column(String(20), index=True)

    notes: Mapped[str | None] = mapped_column(String(1000), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

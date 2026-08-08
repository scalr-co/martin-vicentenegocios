from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import ahora, nuevo_id


class Vehicle(Base):
    """El auto que entra al taller. La patente es la llave de su historial."""

    __tablename__ = "vehicles"

    # Una patente es un solo auto dentro del taller. Repetirla partiria en dos el
    # historial que despues se consulta por patente.
    __table_args__ = (
        UniqueConstraint("workshop_id", "plate", name="uq_vehicles_taller_patente"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=nuevo_id)
    workshop_id: Mapped[str] = mapped_column(ForeignKey("workshops.id"), index=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), index=True)

    # Guardada en mayusculas y sin separadores.
    plate: Mapped[str] = mapped_column(String(12), index=True)

    brand: Mapped[str | None] = mapped_column(String(60), default=None)
    model: Mapped[str | None] = mapped_column(String(60), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

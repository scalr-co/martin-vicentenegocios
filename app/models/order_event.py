from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import ahora, nuevo_id

TIPO_CAMBIO_DE_ESTADO = "cambio_de_estado"


class OrderEvent(Base):
    """Lo que le fue pasando a una orden, y quien lo hizo.

    Responde la pregunta que aparece cuando algo sale mal: quien dio esta orden por
    lista, y cuando. Es un registro que solo crece; no se edita ni se borra.
    """

    __tablename__ = "order_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=nuevo_id)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)

    # Queda en null si el usuario se borra: el evento sobrevive a la persona.
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None)

    type: Mapped[str] = mapped_column(String(40))
    from_status: Mapped[str | None] = mapped_column(String(30), default=None)
    to_status: Mapped[str | None] = mapped_column(String(30), default=None)
    meta: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import ahora, nuevo_id

CANAL_WHATSAPP = "whatsapp"

AVISO_PENDIENTE = "pending"
AVISO_LISTO_PARA_ENVIAR = "link_ready"
AVISO_ENVIADO = "sent"
AVISO_FALLIDO = "failed"


class Notification(Base):
    """Un aviso al cliente. Hoy lo aprieta el mecanico; manana puede salir solo.

    La tabla es la misma en los dos modos. Con `whatsapp_mode = "link"` el aviso queda
    en `link_ready` y el frontend abre wa.me; con `"api"` lo envia el backend y pasa a
    `sent`. Asi el dia que se active el envio automatico no hay que rehacer nada.
    """

    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=nuevo_id)
    workshop_id: Mapped[str] = mapped_column(ForeignKey("workshops.id"), index=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), index=True)

    channel: Mapped[str] = mapped_column(String(20), default=CANAL_WHATSAPP)

    # Se copian el telefono y el texto tal como salieron: si despues cambian la ficha
    # del cliente, el registro tiene que seguir diciendo lo que de verdad se envio.
    to_phone: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(20), default=AVISO_PENDIENTE)

    triggered_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

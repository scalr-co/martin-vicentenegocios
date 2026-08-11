from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import ahora, nuevo_id

ACCION_TALLER_CREADO = "workshop_created"
ACCION_TALLER_EDITADO = "workshop_updated"
ACCION_CLAVE_DEL_DUENO_CAMBIADA = "owner_password_reset"


class AdminAudit(Base):
    """Lo que hizo la administracion de la plataforma, y quien lo hizo.

    Existe por una pregunta que hoy no tiene respuesta: quien entro a que taller. El
    admin puede cambiarle la clave al dueno de cualquier taller -es lo que le devuelve
    el acceso a quien la perdio-, y sin registro el dueno queda fuera sin que nadie
    sepa por que ni quien lo hizo. Con tres personas con acceso, eso deja de ser un
    detalle.

    Es un registro que solo crece: no se edita ni se borra.
    """

    __tablename__ = "admin_audit"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=nuevo_id)

    # Queda en null si la cuenta se borra: el registro sobrevive a la persona.
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None)

    action: Mapped[str] = mapped_column(String(40), index=True)

    # Sobre que se hizo. Se guarda el id suelto y no una relacion: si manana se borra el
    # taller, el registro de lo que se le hizo tiene que quedar igual.
    workshop_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
    target_user_id: Mapped[str | None] = mapped_column(String(36), default=None)

    detail: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

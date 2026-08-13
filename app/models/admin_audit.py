from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import ahora, nuevo_id

ACCION_TALLER_CREADO = "workshop_created"
ACCION_TALLER_EDITADO = "workshop_updated"
ACCION_CLAVE_DEL_DUENO_CAMBIADA = "owner_password_reset"

# Cortarle el acceso a un taller entero no es "una edicion mas": deja a varias personas
# sin poder trabajar. Por eso tiene accion propia y no viaja dentro de workshop_updated.
ACCION_TALLER_SUSPENDIDO = "workshop_suspended"
ACCION_TALLER_REACTIVADO = "workshop_reactivated"
ACCION_TALLER_DADO_DE_BAJA = "workshop_archived"
ACCION_TALLER_RESTAURADO = "workshop_restored"

# Entrar a mirar lo que tiene adentro un taller: sus ordenes, sus clientes, sus avisos.
# No cambia nada, y aun asi se anota: leer los datos de otro tambien es entrar en su casa.
ACCION_TALLER_MIRADO = "workshop_viewed"

# Entrar a crear una cuenta dentro del taller de otro, y tocar las llaves del panel.
ACCION_USUARIO_CREADO = "user_created"
ACCION_CUENTA_ADMIN_CREADA = "admin_created"
ACCION_CUENTA_ADMIN_EDITADA = "admin_updated"


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

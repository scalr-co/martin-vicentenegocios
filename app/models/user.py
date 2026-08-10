from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import ahora, nuevo_id
from app.models.workshop import Workshop

ROL_DUENO = "owner"
ROL_MECANICO = "mechanic"

# Solve, no el taller. Da acceso al panel de administracion y a NADA de los talleres:
# las ordenes, los clientes y los vehiculos siguen filtrando por el taller del token.
ROL_ADMIN_PLATAFORMA = "platform_admin"


class User(Base):
    """Una persona del taller. El dueno administra; el mecanico opera las ordenes."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=nuevo_id)
    workshop_id: Mapped[str] = mapped_column(ForeignKey("workshops.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))

    # Unico en todo el sistema: es con lo que se entra, sin tener que elegir taller.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=ROL_MECANICO)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    # `foreign_keys` explicito: desde que workshops tiene `created_by_user_id`, hay dos
    # caminos entre las dos tablas y SQLAlchemy no puede adivinar cual es "su taller".
    workshop: Mapped[Workshop] = relationship(lazy="joined", foreign_keys=[workshop_id])

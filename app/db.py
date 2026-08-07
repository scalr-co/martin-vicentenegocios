"""Conexion a la base de datos y sesion por peticion."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Padre de todas las tablas."""


motor = create_engine(settings.database_url, pool_pre_ping=True)
FabricaDeSesiones = sessionmaker(bind=motor, expire_on_commit=False)


def obtener_sesion() -> Iterator[Session]:
    """Entrega una sesion por peticion y la cierra al terminar.

    Los tests la reemplazan por una base en memoria.
    """
    with FabricaDeSesiones() as sesion:
        yield sesion

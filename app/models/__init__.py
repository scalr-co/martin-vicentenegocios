"""Todas las tablas se importan aca para que SQLAlchemy las conozca al crear el esquema."""

from app.models.user import ROL_DUENO, ROL_MECANICO, User
from app.models.workshop import MODO_API, MODO_LINK, Workshop

__all__ = ["ROL_DUENO", "ROL_MECANICO", "MODO_API", "MODO_LINK", "User", "Workshop"]

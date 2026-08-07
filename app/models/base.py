"""Piezas comunes a todas las tablas."""

import uuid
from datetime import UTC, datetime


def nuevo_id() -> str:
    """Identificador aleatorio.

    Se usa UUID y no un numero correlativo a proposito: un id adivinable permitiria
    a un taller tantear los identificadores de otro.
    """
    return str(uuid.uuid4())


def ahora() -> datetime:
    return datetime.now(UTC)

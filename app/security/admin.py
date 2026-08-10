"""La clave de administracion del servidor.

Es la llave de arranque: con ella se crean las cuentas de admin de Solve, y nada mas.
El dia a dia -dar de alta talleres, corregirlos- va con la cuenta de cada uno, para que
quede registrado quien hizo que.

Se lee `config.settings` en cada llamada y no al importar, para que los tests puedan
reemplazar los ajustes sin depender del orden en que se importaron los modulos.
"""

import secrets

from fastapi import Header, HTTPException, status

from app import config


def exigir_clave_de_administracion(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> None:
    """Compara en tiempo constante: una comparacion normal filtra la clave letra a letra."""
    esperada = config.settings.admin_api_key
    if not esperada or not secrets.compare_digest(x_admin_key or "", esperada):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operacion es solo para administracion",
        )

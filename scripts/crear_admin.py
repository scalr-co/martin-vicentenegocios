"""Crea una cuenta de administracion de la plataforma.

Se corre en la consola del servidor, no por HTTP:

    python scripts/crear_admin.py --nombre "Vicente" --email vicente@solve.cl

La clave se pide en pantalla, sin mostrarla y dos veces. Existe `--password` para cuando
otro script llama a este, pero a mano conviene no usarlo: lo que se escribe en la linea
de comandos queda en el historial del shell y a la vista en la lista de procesos.

Antes esto era `POST /admin/accounts` con la cabecera `X-Admin-Key` y sin sesion de
nadie. Con esa llave se creaba un admin, se le cambiaba la clave al dueno de cualquier
taller y se entraba a sus datos, sin que quedara registro de quien lo hizo. La llave
raiz sigue existiendo -quien tiene la llave raiz hace cosas de raiz- pero deja de estar
publicada en internet: para usarla hay que estar dentro del servidor.

Las cuentas siguientes las crea un admin ya logueado, por `POST /admin/accounts`. Esta
es solo la primera, la que no puede crear nadie porque todavia no hay con quien entrar.

El alta en si vive en `app/services/altas.py`, compartida con esa ruta: si estuviera
escrita aca tambien, las dos puertas se irian separando.
"""

import argparse
import getpass
import sys
from pathlib import Path

from fastapi import HTTPException

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app.db import FabricaDeSesiones  # noqa: E402
from app.services.altas import (  # noqa: E402
    LARGO_MINIMO_DE_CLAVE_ADMIN as LARGO_MINIMO_DE_CLAVE,
)
from app.services.altas import crear_admin  # noqa: E402

__all__ = ["LARGO_MINIMO_DE_CLAVE", "crear_admin", "main"]


def _clave_escrita_a_ciegas() -> str | None:
    """Pide la clave en pantalla, sin mostrarla. Devuelve None si las dos no calzan.

    No viaja como argumento porque ahi queda escrita en el historial del shell y a la
    vista de cualquiera que liste los procesos del servidor. Se pide dos veces porque se
    teclea sin verla: un dedazo deja creada e inaccesible la cuenta con mas poder del
    sistema, y aca no hay recuperacion de clave en ningun lado.
    """
    primera = getpass.getpass(f"Clave ({LARGO_MINIMO_DE_CLAVE} caracteres o mas): ")
    segunda = getpass.getpass("Otra vez, para confirmar: ")
    return primera if primera == segunda else None


def main() -> int:
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--nombre", required=True)
    argumentos.add_argument("--email", required=True)
    argumentos.add_argument(
        "--password",
        help="Mejor no usarlo: sin esto la clave se pide en pantalla y no queda escrita.",
    )
    opciones = argumentos.parse_args()

    clave = opciones.password or _clave_escrita_a_ciegas()
    if clave is None:
        print("Las dos claves no son iguales. No se creo la cuenta.")
        return 1

    with FabricaDeSesiones() as sesion:
        try:
            admin = crear_admin(sesion, opciones.nombre, opciones.email, clave)
        except HTTPException as error:
            # El alta se comparte con `POST /admin/accounts`, asi que sus fallas vienen
            # con codigo HTTP. Aca no hay navegador que lo lea: se traduce a una linea.
            print(f"No se creo la cuenta: {error.detail}")
            return 1
        sesion.commit()
        print(f"Cuenta de administracion creada: {admin.email}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

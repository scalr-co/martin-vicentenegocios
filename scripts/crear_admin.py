"""Crea una cuenta de administracion de la plataforma.

Se corre en la consola del servidor, no por HTTP:

    python scripts/crear_admin.py --nombre "Vicente" --email vicente@solve.cl --password ...

Antes esto era `POST /admin/accounts` con la cabecera `X-Admin-Key` y sin sesion de
nadie. Con esa llave se creaba un admin, se le cambiaba la clave al dueno de cualquier
taller y se entraba a sus datos, sin que quedara registro de quien lo hizo. La llave
raiz sigue existiendo -quien tiene la llave raiz hace cosas de raiz- pero deja de estar
publicada en internet: para usarla hay que estar dentro del servidor.

Las cuentas siguientes las crea un admin ya logueado; esta es solo la primera.
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app.db import FabricaDeSesiones  # noqa: E402
from app.models import ROL_ADMIN_PLATAFORMA, User  # noqa: E402
from app.security.passwords import hashear  # noqa: E402
from app.services.altas import taller_interno  # noqa: E402

LARGO_MINIMO_DE_CLAVE = 12


class NoSePudoCrear(Exception):
    """El correo ya esta tomado o la clave no sirve."""


def crear_admin(sesion, nombre: str, email: str, clave: str) -> User:
    """Deja la cuenta lista para entrar por /auth/login. No hace commit."""
    if len(clave) < LARGO_MINIMO_DE_CLAVE:
        raise NoSePudoCrear(
            f"La clave necesita al menos {LARGO_MINIMO_DE_CLAVE} caracteres: es la "
            "cuenta con mas poder del sistema."
        )

    email = email.strip().lower()
    if sesion.scalar(select(User).where(User.email == email)) is not None:
        raise NoSePudoCrear(f"Ya hay un usuario con el correo {email}")

    admin = User(
        workshop_id=taller_interno(sesion).id,
        name=nombre.strip(),
        email=email,
        password_hash=hashear(clave),
        role=ROL_ADMIN_PLATAFORMA,
    )
    sesion.add(admin)
    return admin


def main() -> int:
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--nombre", required=True)
    argumentos.add_argument("--email", required=True)
    argumentos.add_argument("--password", required=True)
    opciones = argumentos.parse_args()

    with FabricaDeSesiones() as sesion:
        try:
            admin = crear_admin(sesion, opciones.nombre, opciones.email, opciones.password)
        except NoSePudoCrear as error:
            print(f"No se creo la cuenta: {error}")
            return 1
        sesion.commit()
        print(f"Cuenta de administracion creada: {admin.email}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Guardado y verificacion de contrasenas con bcrypt.

La contrasena en texto plano no se guarda nunca. Lo que va a la base de datos es
el resultado de hashear(), que no se puede revertir.

bcrypt solo admite 72 bytes. En vez de recortar la clave -que dejaria equivalentes
a dos contrasenas largas con el mismo comienzo- la resumimos antes con SHA-256:
el resumen siempre mide 44 bytes en base64 y depende de la clave completa.
"""

import base64
import hashlib

import bcrypt


def _preparar(clave: str) -> bytes:
    resumen = hashlib.sha256(clave.encode("utf-8")).digest()
    return base64.b64encode(resumen)


def hashear(clave: str) -> str:
    return bcrypt.hashpw(_preparar(clave), bcrypt.gensalt()).decode("utf-8")


def verificar(clave: str, guardado: str) -> bool:
    return bcrypt.checkpw(_preparar(clave), guardado.encode("utf-8"))

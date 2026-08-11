"""Freno a quien prueba contrasenas una tras otra.

Sin esto, 20 intentos fallidos seguidos son 20 veces 401 y el unico limite es lo que
tarda bcrypt. Los correos de un negocio son adivinables y la contrasena es el unico
factor que hay.

El registro vive en la memoria del proceso. Motor Ping corre en una sola instancia, asi
que alcanza; se pierde al reiniciar -y con un despliegue, el contador vuelve a cero- y
no sirve si algun dia hay dos replicas. Cuando eso pase hay que moverlo a la base o a
un Redis; queda escrito aca para que no se descubra el dia equivocado.
"""

from collections import defaultdict
from datetime import UTC, datetime, timedelta

# Por correo: quien apunta a una cuenta concreta.
LIMITE_POR_CUENTA = 10

# Por direccion, mas alto: en un taller todos salen por la misma IP, y equivocarse
# escribiendo la clave del computador del mesón no puede dejar fuera a los demas.
LIMITE_POR_DIRECCION = 30

VENTANA = timedelta(minutes=15)

_fallos: dict[str, list[datetime]] = defaultdict(list)


def _recientes(clave: str, ahora: datetime) -> list[datetime]:
    """Los intentos que todavia cuentan. De paso limpia los que ya vencieron."""
    vigentes = [momento for momento in _fallos[clave] if ahora - momento < VENTANA]
    if vigentes:
        _fallos[clave] = vigentes
    else:
        _fallos.pop(clave, None)
    return vigentes


def demasiados_intentos(correo: str, direccion: str) -> bool:
    ahora = datetime.now(UTC)
    return (
        len(_recientes(f"correo:{correo}", ahora)) >= LIMITE_POR_CUENTA
        or len(_recientes(f"ip:{direccion}", ahora)) >= LIMITE_POR_DIRECCION
    )


def registrar_fallo(correo: str, direccion: str) -> None:
    ahora = datetime.now(UTC)
    _fallos[f"correo:{correo}"].append(ahora)
    _fallos[f"ip:{direccion}"].append(ahora)


def olvidar(correo: str, direccion: str) -> None:
    """Entrar bien borra la cuenta pendiente: el que se equivoco tres veces y despues
    se acordo de su clave no arrastra esos tres intentos toda la tarde."""
    _fallos.pop(f"correo:{correo}", None)
    _fallos.pop(f"ip:{direccion}", None)


def limpiar_todo() -> None:
    """Solo para los tests: el registro es global y se filtraria de uno a otro."""
    _fallos.clear()

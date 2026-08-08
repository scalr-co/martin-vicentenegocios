"""Deja telefonos y patentes en un unico formato antes de guardarlos.

Sin esto, "ABCD12" y "abcd 12" serian dos autos distintos y el historial del vehiculo
quedaria partido. Con los telefonos pasa lo mismo y ademas rompe el link de wa.me.
"""

import re

CODIGO_CHILE = "56"
LARGO_MINIMO_DE_TELEFONO = 8
LARGO_DE_MOVIL_CHILENO = 9


class DatoInvalido(ValueError):
    """El valor no tiene la forma minima para poder guardarse."""


def normalizar_telefono(texto: str) -> str:
    """Devuelve solo digitos, con codigo de pais. Formato que espera wa.me."""
    digitos = re.sub(r"\D", "", texto or "")

    if not digitos:
        raise DatoInvalido("El telefono viene vacio")

    # En Chile la gente escribe su celular como "9 1234 5678", sin el codigo de pais.
    if len(digitos) == LARGO_DE_MOVIL_CHILENO and digitos.startswith("9"):
        digitos = CODIGO_CHILE + digitos

    if len(digitos) < LARGO_MINIMO_DE_TELEFONO:
        raise DatoInvalido(f"El telefono '{texto}' tiene muy pocos digitos")

    return digitos


def normalizar_patente(texto: str) -> str:
    """Mayusculas, sin espacios ni guiones."""
    limpia = re.sub(r"[^A-Za-z0-9]", "", texto or "").upper()

    if not limpia:
        raise DatoInvalido("La patente viene vacia")

    return limpia

"""Deja telefonos, patentes y ruts en un unico formato antes de guardarlos.

Sin esto, "ABCD12" y "abcd 12" serian dos autos distintos y el historial del vehiculo
quedaria partido. Con los telefonos pasa lo mismo y ademas rompe el link de wa.me.
"""

import re

CODIGO_CHILE = "56"
LARGO_MINIMO_DE_TELEFONO = 8
LARGO_DE_MOVIL_CHILENO = 9

# Un rut chileno tiene 7 u 8 digitos. Se deja holgura: 6 para los ruts viejos de los
# clientes mas grandes, 9 por si el registro civil algun dia llega ahi.
LARGO_MINIMO_DEL_CUERPO = 6
LARGO_MAXIMO_DEL_CUERPO = 9


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


def _digito_verificador(cuerpo: str) -> str:
    """Modulo 11: la cuenta con la que el registro civil arma el digito del rut."""
    suma = 0
    factor = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * factor
        factor = 2 if factor == 7 else factor + 1

    resto = 11 - suma % 11
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def normalizar_rut(texto: str) -> str:
    """Sin puntos, con guion y K mayuscula: "12.345.678-5" queda "12345678-5".

    Ademas comprueba el digito verificador. Es lo unico que caza un rut mal tecleado
    antes de que quede pegado a la ficha del cliente.
    """
    limpio = re.sub(r"[^0-9kK]", "", texto or "").upper()

    if not limpio:
        raise DatoInvalido("El rut viene vacio")

    cuerpo, verificador = limpio[:-1], limpio[-1]

    if not cuerpo.isdigit():
        raise DatoInvalido(f"El rut '{texto}' tiene algo que no es un numero")

    if not LARGO_MINIMO_DEL_CUERPO <= len(cuerpo) <= LARGO_MAXIMO_DEL_CUERPO:
        raise DatoInvalido(f"El rut '{texto}' no tiene la cantidad de digitos de un rut")

    if verificador != _digito_verificador(cuerpo):
        raise DatoInvalido(f"El rut '{texto}' esta mal escrito: no calza el verificador")

    return f"{cuerpo}-{verificador}"

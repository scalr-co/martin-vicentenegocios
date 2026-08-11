"""Deja telefonos, patentes y ruts en un unico formato antes de guardarlos.

Sin esto, "ABCD12" y "abcd 12" serian dos autos distintos y el historial del vehiculo
quedaria partido. Con los telefonos pasa lo mismo y ademas rompe el link de wa.me.
"""

import re

CODIGO_CHILE = "56"

# Todo numero chileno tiene 9 digitos despues del codigo de pais: el celular parte en 9
# y el fijo en su codigo de area (2 en Santiago, 45 en Temuco, 41 en Concepcion...).
LARGO_NACIONAL = 9
INICIOS_DE_NUMERO_CHILENO = "23456789"

# Un rut chileno tiene 7 u 8 digitos. Se deja holgura: 6 para los ruts viejos de los
# clientes mas grandes, 9 por si el registro civil algun dia llega ahi.
LARGO_MINIMO_DEL_CUERPO = 6
LARGO_MAXIMO_DEL_CUERPO = 9


class DatoInvalido(ValueError):
    """El valor no tiene la forma minima para poder guardarse."""


def normalizar_telefono(texto: str) -> str:
    """Devuelve 56 y los 9 digitos nacionales. Formato que espera wa.me.

    Lo que no sea un numero chileno se rechaza en vez de guardarse tal cual. Antes se
    guardaba: el taller anotaba el fijo como se lo dictaron ("45 234 5678"), el sistema
    armaba el aviso con normalidad y el link apuntaba a un numero que no existe. El
    taller creia que habia avisado y el cliente nunca supo nada.
    """
    digitos = re.sub(r"\D", "", texto or "")

    if not digitos:
        raise DatoInvalido("El telefono viene vacio")

    # "0056 9 1234 5678": el prefijo internacional como se marca desde un fijo.
    if digitos.startswith("00"):
        digitos = digitos[2:]

    if len(digitos) == LARGO_NACIONAL + 2 and digitos.startswith(CODIGO_CHILE):
        nacional = digitos[2:]
    elif len(digitos) == LARGO_NACIONAL + 1 and digitos.startswith("0"):
        # El 0 de la marcacion larga de antes, que alguna gente sigue anotando.
        nacional = digitos[1:]
    elif len(digitos) == LARGO_NACIONAL:
        # Como lo escribe la gente aca: "9 1234 5678" o "45 234 5678".
        nacional = digitos
    else:
        raise DatoInvalido(
            f"El telefono '{texto}' no es un numero chileno: tiene que tener 9 digitos, "
            "con o sin el +56 adelante"
        )

    if nacional[0] not in INICIOS_DE_NUMERO_CHILENO:
        raise DatoInvalido(f"El telefono '{texto}' no empieza como un numero chileno")

    return CODIGO_CHILE + nacional


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

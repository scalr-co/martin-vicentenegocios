"""Los datos entran como los escribe la gente y se guardan en un solo formato.

Si no se normaliza, "ABCD12", "abcd12" y "ABCD 12" son tres autos distintos para la
base de datos, y el historial del vehiculo se parte en pedazos.
"""

import pytest

from app.services.normalizacion import (
    DatoInvalido,
    normalizar_patente,
    normalizar_telefono,
)


@pytest.mark.parametrize(
    "escrito, guardado",
    [
        ("56912345678", "56912345678"),
        ("+56912345678", "56912345678"),
        ("+56 9 1234 5678", "56912345678"),
        ("(56) 9-1234-5678", "56912345678"),
    ],
)
def test_el_telefono_se_guarda_solo_con_digitos(escrito, guardado):
    assert normalizar_telefono(escrito) == guardado


def test_un_telefono_chileno_sin_codigo_de_pais_lo_recibe():
    """En Chile la gente escribe su numero como 9 1234 5678."""
    assert normalizar_telefono("9 1234 5678") == "56912345678"


def test_un_telefono_sin_digitos_suficientes_se_rechaza():
    with pytest.raises(DatoInvalido):
        normalizar_telefono("123")


def test_un_telefono_vacio_se_rechaza():
    with pytest.raises(DatoInvalido):
        normalizar_telefono("   ")


@pytest.mark.parametrize(
    "escrita, guardada",
    [
        ("ABCD12", "ABCD12"),
        ("abcd12", "ABCD12"),
        ("ABCD 12", "ABCD12"),
        (" ab-cd.12 ", "ABCD12"),
    ],
)
def test_la_patente_se_guarda_en_mayusculas_y_sin_separadores(escrita, guardada):
    assert normalizar_patente(escrita) == guardada


def test_una_patente_vacia_se_rechaza():
    with pytest.raises(DatoInvalido):
        normalizar_patente("  ")

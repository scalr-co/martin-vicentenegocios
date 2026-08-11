"""Los datos entran como los escribe la gente y se guardan en un solo formato.

Si no se normaliza, "ABCD12", "abcd12" y "ABCD 12" son tres autos distintos para la
base de datos, y el historial del vehiculo se parte en pedazos.
"""

import pytest

from app.services.normalizacion import (
    DatoInvalido,
    normalizar_patente,
    normalizar_rut,
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


@pytest.mark.parametrize(
    "escrito, guardado",
    [
        ("452345678", "56452345678"),
        ("45 234 5678", "56452345678"),
        ("+56 45 234 5678", "56452345678"),
        ("223456789", "56223456789"),
        ("0056912345678", "56912345678"),
    ],
)
def test_un_fijo_chileno_tambien_queda_en_formato_de_wame(escrito, guardado):
    """El taller anota el fijo como se lo dictaron.

    Antes se guardaba tal cual, sin el 56 adelante: el link de wa.me apuntaba a un
    numero que no existe y el taller creia que habia avisado.
    """
    assert normalizar_telefono(escrito) == guardado


@pytest.mark.parametrize(
    "basura",
    [
        "22345678",
        "999999999999999",
        "+1 555 0123",
        "123",
        "123456789",
    ],
)
def test_lo_que_no_es_un_telefono_chileno_se_rechaza(basura):
    """Guardar un numero que no sirve es peor que no dejar guardarlo."""
    with pytest.raises(DatoInvalido):
        normalizar_telefono(basura)


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


@pytest.mark.parametrize(
    "escrito, guardado",
    [
        ("12.345.678-5", "12345678-5"),
        ("12345678-5", "12345678-5"),
        ("123456785", "12345678-5"),
        (" 12.345.678 - 5 ", "12345678-5"),
    ],
)
def test_el_rut_se_guarda_sin_puntos_y_con_guion(escrito, guardado):
    assert normalizar_rut(escrito) == guardado


def test_el_digito_verificador_k_se_guarda_en_mayuscula():
    assert normalizar_rut("12.345.698-k") == "12345698-K"


def test_un_rut_con_digito_verificador_cero_se_acepta():
    assert normalizar_rut("12.345.658-0") == "12345658-0"


def test_un_rut_con_el_digito_verificador_equivocado_se_rechaza():
    """Para eso existe el verificador: caza el numero mal tecleado."""
    with pytest.raises(DatoInvalido):
        normalizar_rut("12.345.678-9")


def test_un_rut_vacio_se_rechaza():
    with pytest.raises(DatoInvalido):
        normalizar_rut("   ")


def test_un_rut_demasiado_corto_se_rechaza():
    with pytest.raises(DatoInvalido):
        normalizar_rut("123-6")


def test_un_rut_con_letras_en_el_cuerpo_se_rechaza():
    with pytest.raises(DatoInvalido):
        normalizar_rut("12.34A.678-5")

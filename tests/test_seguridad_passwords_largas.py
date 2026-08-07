"""bcrypt solo considera los primeros 72 bytes de la clave.

Sin tratamiento previo, dos contrasenas largas que coincidan en ese tramo quedan
equivalentes: quien sepa la primera entra con la segunda. Estos tests fijan que eso
no pase y que una clave larga tampoco haga reventar el registro.
"""

from app.security.passwords import hashear, verificar


def test_una_clave_mas_larga_que_el_limite_de_bcrypt_funciona():
    larga = "c" * 200

    assert verificar(larga, hashear(larga)) is True


def test_dos_claves_que_solo_difieren_despues_del_byte_72_no_se_confunden():
    prefijo = "c" * 72

    guardado = hashear(prefijo + "PRIMERA")

    assert verificar(prefijo + "SEGUNDA", guardado) is False

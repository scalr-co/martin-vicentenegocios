from app.security.passwords import hashear, verificar


def test_el_hash_no_es_la_contrasena_original():
    resultado = hashear("clave-del-taller")

    assert resultado != "clave-del-taller"


def test_verificar_acepta_la_contrasena_correcta():
    guardado = hashear("clave-del-taller")

    assert verificar("clave-del-taller", guardado) is True


def test_verificar_rechaza_una_contrasena_incorrecta():
    guardado = hashear("clave-del-taller")

    assert verificar("otra-clave", guardado) is False


def test_dos_hashes_de_la_misma_contrasena_son_distintos():
    """Cada hash lleva su propia sal: dos usuarios con la misma clave no se delatan entre si."""
    assert hashear("misma-clave") != hashear("misma-clave")

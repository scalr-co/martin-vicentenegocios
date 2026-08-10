"""Como se ve el texto que sale del taller hacia afuera.

El mecanico escribe rapido y con una mano: "juan perez", "nissan". Eso esta bien, es su
ficha. Lo que no puede pasar es que el cliente reciba un WhatsApp que diga "Hola juan,
tu nissan esta listo" -se lee como un mensaje descuidado de un taller descuidado-.

Se corrige al mostrar y no al guardar, para no perder lo que el mecanico escribio.
"""

from app.services.presentacion import (
    describir_para_el_cliente,
    describir_vehiculo,
    primer_nombre,
)


def test_el_nombre_va_con_mayuscula_aunque_lo_escriban_apurado():
    assert primer_nombre("juan perez") == "Juan"


def test_no_se_inventan_tildes():
    """De "perez" no se puede deducir "Perez" o "Perez": adivinar seria peor."""
    assert primer_nombre("perez") == "Perez"


def test_un_nombre_ya_bien_escrito_no_se_toca():
    assert primer_nombre("María José Fuentes") == "María"


def test_la_marca_va_con_mayuscula():
    assert describir_para_el_cliente("ABCD12", "nissan", "v16") == "Nissan v16 (ABCD12)"


def test_las_marcas_que_se_escriben_en_mayusculas_se_respetan():
    """`.title()` las dejaria como "Bmw", que se ve peor que no haber hecho nada."""
    assert describir_para_el_cliente("ABCD12", "bmw", "x3") == "BMW x3 (ABCD12)"


def test_el_modelo_queda_como_lo_escribio_el_mecanico():
    """No hay regla que sirva para CX-5, RAV4 e i10 a la vez. Inventar seria peor."""
    assert describir_para_el_cliente("ABCD12", "mazda", "CX-5") == "Mazda CX-5 (ABCD12)"


def test_la_pantalla_del_mecanico_se_ve_igual_que_el_mensaje():
    """Si solo se corrigiera el WhatsApp, los dos textos empezarian a separarse."""
    assert describir_vehiculo("ABCD12", "nissan", "v16") == "Nissan v16 · Patente ABCD12"


def test_sin_marca_ni_modelo_sigue_saliendo_la_patente():
    assert describir_para_el_cliente("ABCD12", None, None) == "vehiculo (patente ABCD12)"

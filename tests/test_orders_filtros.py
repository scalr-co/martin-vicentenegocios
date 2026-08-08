"""Encontrar una orden en el panel.

El mecanico no busca por id: mira la patente del auto que tiene al lado, o se acuerda del
apellido del cliente. Con veinte ordenes abiertas, sin esto hay que leerlas todas.
"""

from tests.conftest import con_token, crear_cliente_api, crear_vehiculo_api, entrar


def orden_de(cliente, token, nombre, telefono, patente, titulo="Revision"):
    cliente_id = crear_cliente_api(cliente, token, nombre=nombre, telefono=telefono)
    vehiculo_id = crear_vehiculo_api(cliente, token, cliente_id, patente=patente)
    respuesta = cliente.post(
        "/orders",
        json={"clientId": cliente_id, "vehicleId": vehiculo_id, "title": titulo},
        headers=con_token(token),
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["data"]["id"]


def dos_ordenes(cliente, token):
    """Juan con su ABCD12 y Maria con su XYZW99."""
    de_juan = orden_de(cliente, token, "Juan Perez", "56911111111", "ABCD12")
    de_maria = orden_de(cliente, token, "Maria Soto", "56922222222", "XYZW99")
    return de_juan, de_maria


def buscar(cliente, token, **filtros):
    respuesta = cliente.get("/orders", params=filtros, headers=con_token(token))
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def test_buscar_por_patente(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    de_juan, _ = dos_ordenes(cliente, token)

    encontradas = buscar(cliente, token, search="ABCD12")["data"]

    assert [o["id"] for o in encontradas] == [de_juan]


def test_buscar_por_patente_sin_importar_como_se_escriba(cliente, dueno):
    """El mecanico escribe rapido y en minusculas."""
    token = entrar(cliente, "dueno@taller.cl")
    de_juan, _ = dos_ordenes(cliente, token)

    encontradas = buscar(cliente, token, search="abcd12")["data"]

    assert [o["id"] for o in encontradas] == [de_juan]


def test_buscar_por_nombre_del_cliente(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    _, de_maria = dos_ordenes(cliente, token)

    encontradas = buscar(cliente, token, search="maria")["data"]

    assert [o["id"] for o in encontradas] == [de_maria]


def test_buscar_por_un_pedazo_de_la_patente(cliente, dueno):
    """Se acuerda del final de la patente, no de la patente entera."""
    token = entrar(cliente, "dueno@taller.cl")
    _, de_maria = dos_ordenes(cliente, token)

    encontradas = buscar(cliente, token, search="W99")["data"]

    assert [o["id"] for o in encontradas] == [de_maria]


def test_el_total_cuenta_lo_filtrado_y_no_todo(cliente, dueno):
    """Si el total ignorara el filtro, el paginador del frontend mostraria paginas vacias."""
    token = entrar(cliente, "dueno@taller.cl")
    dos_ordenes(cliente, token)

    resultado = buscar(cliente, token, search="ABCD12")

    assert resultado["meta"]["total"] == 1


def test_filtrar_por_estado(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    de_juan, _ = dos_ordenes(cliente, token)
    cliente.post(
        f"/orders/{de_juan}/status", json={"status": "listo"}, headers=con_token(token)
    )

    encontradas = buscar(cliente, token, status="listo")["data"]

    assert [o["id"] for o in encontradas] == [de_juan]


def test_un_estado_inventado_se_rechaza(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = cliente.get(
        "/orders", params={"status": "lavandolo"}, headers=con_token(token)
    )

    assert respuesta.status_code == 422


def test_se_puede_buscar_dentro_de_las_abiertas(cliente, dueno):
    """Los filtros se suman: lo que tengo entre manos, del cliente que pregunta."""
    token = entrar(cliente, "dueno@taller.cl")
    de_juan, _ = dos_ordenes(cliente, token)
    cliente.post(
        f"/orders/{de_juan}/status", json={"status": "entregado"}, headers=con_token(token)
    )

    encontradas = buscar(cliente, token, search="ABCD12", open=True)["data"]

    assert encontradas == []


def test_la_busqueda_no_cruza_talleres(cliente, dueno, dueno_vecino):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    dos_ordenes(cliente, token_propio)

    encontradas = buscar(cliente, token_vecino, search="ABCD12")["data"]

    assert encontradas == []

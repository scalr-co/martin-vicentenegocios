from tests.conftest import con_token, entrar


def crear_cliente(
    cliente, token, nombre="Juan Perez", telefono="56911111111", notas=None, rut=None
):
    cuerpo = {"name": nombre, "phone": telefono}
    if notas is not None:
        cuerpo["notes"] = notas
    if rut is not None:
        cuerpo["rut"] = rut
    return cliente.post("/clients", json=cuerpo, headers=con_token(token))


def test_crear_un_cliente_lo_devuelve_con_su_id(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = crear_cliente(cliente, token, nombre="Juan Perez")

    assert respuesta.status_code == 201
    datos = respuesta.json()["data"]
    assert datos["id"]
    assert datos["name"] == "Juan Perez"


def test_el_telefono_se_guarda_normalizado(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = crear_cliente(cliente, token, telefono="+56 9 1111 1111")

    assert respuesta.json()["data"]["phone"] == "56911111111"


def test_listar_clientes_devuelve_la_forma_de_lista_del_contrato(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    crear_cliente(cliente, token)

    respuesta = cliente.get("/clients", headers=con_token(token))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert isinstance(cuerpo["data"], list)
    assert cuerpo["meta"] == {"page": 1, "limit": 20, "total": 1}


def test_un_taller_no_ve_los_clientes_del_otro(cliente, dueno, dueno_vecino):
    """El test mas importante del sistema."""
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    crear_cliente(cliente, token_propio, nombre="Cliente Propio")

    respuesta = cliente.get("/clients", headers=con_token(token_vecino))

    assert respuesta.json()["data"] == []


def test_pedir_el_cliente_de_otro_taller_responde_no_encontrado(cliente, dueno, dueno_vecino):
    """404 y no 403: confirmar que existe ya seria contar de mas."""
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    ajeno = crear_cliente(cliente, token_propio).json()["data"]["id"]

    respuesta = cliente.get(f"/clients/{ajeno}", headers=con_token(token_vecino))

    assert respuesta.status_code == 404


def test_editar_el_cliente_de_otro_taller_tampoco_se_puede(cliente, dueno, dueno_vecino):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    ajeno = crear_cliente(cliente, token_propio).json()["data"]["id"]

    respuesta = cliente.patch(
        f"/clients/{ajeno}",
        json={"name": "Nombre Cambiado"},
        headers=con_token(token_vecino),
    )

    assert respuesta.status_code == 404


def test_el_mismo_telefono_en_dos_talleres_distintos_esta_permitido(
    cliente, dueno, dueno_vecino
):
    """Una persona puede ser cliente de dos talleres."""
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    crear_cliente(cliente, token_propio, telefono="56922222222")

    respuesta = crear_cliente(cliente, token_vecino, telefono="56922222222")

    assert respuesta.status_code == 201


def test_repetir_el_telefono_dentro_del_mismo_taller_se_rechaza(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    crear_cliente(cliente, token, telefono="56933333333")

    respuesta = crear_cliente(cliente, token, nombre="Otro Nombre", telefono="56933333333")

    assert respuesta.status_code == 409


def test_buscar_por_nombre(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    crear_cliente(cliente, token, nombre="Juan Perez", telefono="56911111111")
    crear_cliente(cliente, token, nombre="Maria Soto", telefono="56922222222")

    respuesta = cliente.get("/clients", params={"search": "maria"}, headers=con_token(token))

    encontrados = respuesta.json()["data"]
    assert [c["name"] for c in encontrados] == ["Maria Soto"]


def test_buscar_por_telefono(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    crear_cliente(cliente, token, nombre="Juan Perez", telefono="56911111111")
    crear_cliente(cliente, token, nombre="Maria Soto", telefono="56922222222")

    respuesta = cliente.get("/clients", params={"search": "2222"}, headers=con_token(token))

    assert [c["name"] for c in respuesta.json()["data"]] == ["Maria Soto"]


def test_sin_token_no_se_puede_listar(cliente, dueno):
    respuesta = cliente.get("/clients")

    assert respuesta.status_code == 401


def test_editar_un_cliente_propio_funciona(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    creado = crear_cliente(cliente, token).json()["data"]["id"]

    respuesta = cliente.patch(
        f"/clients/{creado}",
        json={"notes": "Prefiere que lo llamen en la tarde"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["notes"] == "Prefiere que lo llamen en la tarde"


def test_el_rut_se_guarda_normalizado(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = crear_cliente(cliente, token, rut="12.345.678-5")

    assert respuesta.status_code == 201
    assert respuesta.json()["data"]["rut"] == "12345678-5"


def test_el_rut_es_opcional_y_sin_el_la_ficha_queda_igual(cliente, dueno):
    """La mayoria de los autos entran al taller sin que nadie pida el rut."""
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = crear_cliente(cliente, token)

    assert respuesta.status_code == 201
    assert respuesta.json()["data"]["rut"] is None


def test_un_nombre_de_puros_espacios_se_rechaza(cliente, dueno):
    """Tres espacios miden 3, pasaban el minimo de 2, y la ficha quedaba en blanco.

    El taller terminaba con un cliente que se ve vacio en la lista y no se puede buscar.
    """
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = crear_cliente(cliente, token, nombre="   ")

    assert respuesta.status_code == 422


def test_un_nombre_de_puros_espacios_tampoco_entra_al_editar(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    creado = crear_cliente(cliente, token).json()["data"]["id"]

    respuesta = cliente.patch(
        f"/clients/{creado}", json={"name": "  "}, headers=con_token(token)
    )

    assert respuesta.status_code == 422


def test_el_nombre_se_guarda_sin_los_espacios_de_los_bordes(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = crear_cliente(cliente, token, nombre="  Juan Perez  ")

    assert respuesta.json()["data"]["name"] == "Juan Perez"


def test_un_rut_mal_escrito_no_entra_a_la_ficha(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = crear_cliente(cliente, token, rut="12.345.678-9")

    assert respuesta.status_code == 422


def test_el_rut_se_puede_agregar_despues(cliente, dueno):
    """El mecanico lo pide recien cuando hay que hacer la boleta."""
    token = entrar(cliente, "dueno@taller.cl")
    creado = crear_cliente(cliente, token).json()["data"]["id"]

    respuesta = cliente.patch(
        f"/clients/{creado}",
        json={"rut": "12.345.678-5"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["rut"] == "12345678-5"


def test_buscar_por_rut(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    crear_cliente(cliente, token, nombre="Juan Perez", telefono="56911111111")
    crear_cliente(
        cliente, token, nombre="Maria Soto", telefono="56922222222", rut="12.345.678-5"
    )

    respuesta = cliente.get("/clients", params={"search": "12345678"}, headers=con_token(token))

    assert [c["name"] for c in respuesta.json()["data"]] == ["Maria Soto"]


def test_buscar_por_rut_da_igual_como_se_escriba(cliente, dueno):
    """Lo copia y pega con puntos desde la boleta anterior."""
    token = entrar(cliente, "dueno@taller.cl")
    crear_cliente(cliente, token, nombre="Maria Soto", rut="12345678-5")

    respuesta = cliente.get(
        "/clients", params={"search": "12.345.678-5"}, headers=con_token(token)
    )

    assert [c["name"] for c in respuesta.json()["data"]] == ["Maria Soto"]


def test_el_limite_de_pagina_no_puede_pasarse_del_tope(cliente, dueno):
    """Sin tope, alguien pide limit=1000000 y se lleva la base entera de una."""
    token = entrar(cliente, "dueno@taller.cl")

    respuesta = cliente.get("/clients", params={"limit": 5000}, headers=con_token(token))

    assert respuesta.status_code == 422

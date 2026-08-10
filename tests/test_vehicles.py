"""Los vehiculos del taller, colgados de un cliente.

La patente es la llave del historial: por eso se guarda normalizada y no se repite
dentro del mismo taller.
"""

from tests.conftest import con_token, entrar


def crear_cliente(cliente, token, nombre="Juan Perez", telefono="56911111111"):
    respuesta = cliente.post(
        "/clients",
        json={"name": nombre, "phone": telefono},
        headers=con_token(token),
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["data"]["id"]


def crear_vehiculo(cliente, token, client_id, patente="ABCD12", marca=None, modelo=None):
    cuerpo = {"clientId": client_id, "plate": patente}
    if marca is not None:
        cuerpo["brand"] = marca
    if modelo is not None:
        cuerpo["model"] = modelo
    return cliente.post("/vehicles", json=cuerpo, headers=con_token(token))


def test_crear_un_vehiculo_lo_devuelve_con_su_id(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente(cliente, token)

    respuesta = crear_vehiculo(cliente, token, cliente_id, marca="Toyota", modelo="Corolla")

    assert respuesta.status_code == 201
    datos = respuesta.json()["data"]
    assert datos["id"]
    assert datos["plate"] == "ABCD12"
    assert datos["clientId"] == cliente_id


def test_la_patente_se_guarda_normalizada(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente(cliente, token)

    respuesta = crear_vehiculo(cliente, token, cliente_id, patente=" ab-cd.12 ")

    assert respuesta.json()["data"]["plate"] == "ABCD12"


def test_una_patente_vacia_se_rechaza(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente(cliente, token)

    respuesta = crear_vehiculo(cliente, token, cliente_id, patente="   ")

    assert respuesta.status_code == 422


def test_la_api_devuelve_el_vehiculo_ya_escrito_para_mostrar(cliente, dueno):
    """El frontend imprime esto tal cual; armarlo aca evita que Martin lo repita."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente(cliente, token)

    respuesta = crear_vehiculo(cliente, token, cliente_id, marca="Toyota", modelo="Corolla")

    assert respuesta.json()["data"]["vehicleOrItem"] == "Toyota Corolla · Patente ABCD12"


def test_sin_marca_ni_modelo_igual_se_puede_mostrar(cliente, dueno):
    """A veces el mecanico solo anota la patente y hay que seguir igual."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente(cliente, token)

    respuesta = crear_vehiculo(cliente, token, cliente_id)

    assert respuesta.json()["data"]["vehicleOrItem"] == "Patente ABCD12"


def test_listar_los_vehiculos_de_un_cliente(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    uno = crear_cliente(cliente, token, nombre="Juan Perez", telefono="56911111111")
    otro = crear_cliente(cliente, token, nombre="Maria Soto", telefono="56922222222")
    crear_vehiculo(cliente, token, uno, patente="AAAA11")
    crear_vehiculo(cliente, token, otro, patente="BBBB22")

    respuesta = cliente.get(
        "/vehicles", params={"clientId": uno}, headers=con_token(token)
    )

    assert [v["plate"] for v in respuesta.json()["data"]] == ["AAAA11"]


def test_buscar_por_patente_encuentra_el_auto_que_ya_estuvo_en_el_taller(cliente, dueno):
    """El caso normal de un taller: el auto vuelve.

    Sin esta busqueda no hay forma de llegar al vehiculo desde la patente, que es el
    unico dato que el mecanico tiene en la mano cuando el auto entra por la puerta.
    """
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente(cliente, token)
    crear_vehiculo(cliente, token, cliente_id, patente="AAAA11")
    crear_vehiculo(cliente, token, cliente_id, patente="BBBB22")

    respuesta = cliente.get("/vehicles", params={"plate": "BBBB22"}, headers=con_token(token))

    assert [v["plate"] for v in respuesta.json()["data"]] == ["BBBB22"]


def test_la_patente_se_busca_como_se_guarda_no_como_se_escribe(cliente, dueno):
    """El mecanico escribe "bbbb 22" con una mano. Se guarda normalizada; buscar tambien."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente(cliente, token)
    crear_vehiculo(cliente, token, cliente_id, patente="AAAA11")
    crear_vehiculo(cliente, token, cliente_id, patente="BBBB22")

    respuesta = cliente.get("/vehicles", params={"plate": "bbbb 22"}, headers=con_token(token))

    assert [v["plate"] for v in respuesta.json()["data"]] == ["BBBB22"]


def test_una_patente_que_no_existe_devuelve_la_lista_vacia(cliente, dueno):
    """Es la senal de "auto nuevo": el frontend crea el vehiculo recien cuando ve esto."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente(cliente, token)
    crear_vehiculo(cliente, token, cliente_id, patente="AAAA11")

    respuesta = cliente.get("/vehicles", params={"plate": "ZZZZ99"}, headers=con_token(token))

    assert respuesta.status_code == 200
    assert respuesta.json()["data"] == []


def test_la_patente_de_otro_taller_no_aparece(cliente, dueno, dueno_vecino):
    """Dos talleres pueden atender el mismo auto sin enterarse el uno del otro."""
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    ajeno = crear_cliente(cliente, token_vecino, telefono="56999999999")
    crear_vehiculo(cliente, token_vecino, ajeno, patente="CCCC33")

    respuesta = cliente.get("/vehicles", params={"plate": "CCCC33"}, headers=con_token(token_propio))

    assert respuesta.json()["data"] == []


def test_listar_devuelve_la_forma_de_lista_del_contrato(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente(cliente, token)
    crear_vehiculo(cliente, token, cliente_id)

    respuesta = cliente.get("/vehicles", headers=con_token(token))

    assert respuesta.status_code == 200
    assert respuesta.json()["meta"] == {"page": 1, "limit": 20, "total": 1}


def test_un_taller_no_ve_los_vehiculos_del_otro(cliente, dueno, dueno_vecino):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    cliente_id = crear_cliente(cliente, token_propio)
    crear_vehiculo(cliente, token_propio, cliente_id)

    respuesta = cliente.get("/vehicles", headers=con_token(token_vecino))

    assert respuesta.json()["data"] == []


def test_pedir_el_vehiculo_de_otro_taller_responde_no_encontrado(cliente, dueno, dueno_vecino):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    cliente_id = crear_cliente(cliente, token_propio)
    ajeno = crear_vehiculo(cliente, token_propio, cliente_id).json()["data"]["id"]

    respuesta = cliente.get(f"/vehicles/{ajeno}", headers=con_token(token_vecino))

    assert respuesta.status_code == 404


def test_no_se_puede_colgar_un_vehiculo_del_cliente_de_otro_taller(
    cliente, dueno, dueno_vecino
):
    """Sin esto, mandando ids ajenos se podria escribir dentro del taller del vecino."""
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    cliente_ajeno = crear_cliente(cliente, token_propio)

    respuesta = crear_vehiculo(cliente, token_vecino, cliente_ajeno)

    assert respuesta.status_code == 404


def test_repetir_la_patente_dentro_del_mismo_taller_se_rechaza(cliente, dueno):
    """Dos fichas de la misma patente parten el historial del auto en dos."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente(cliente, token)
    crear_vehiculo(cliente, token, cliente_id, patente="ABCD12")

    respuesta = crear_vehiculo(cliente, token, cliente_id, patente="abcd 12")

    assert respuesta.status_code == 409


def test_la_misma_patente_en_dos_talleres_distintos_esta_permitida(
    cliente, dueno, dueno_vecino
):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    crear_vehiculo(cliente, token_propio, crear_cliente(cliente, token_propio))

    respuesta = crear_vehiculo(cliente, token_vecino, crear_cliente(cliente, token_vecino))

    assert respuesta.status_code == 201


def test_editar_un_vehiculo_propio_funciona(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente(cliente, token)
    vehiculo = crear_vehiculo(cliente, token, cliente_id).json()["data"]["id"]

    respuesta = cliente.patch(
        f"/vehicles/{vehiculo}",
        json={"brand": "Nissan", "model": "V16"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["brand"] == "Nissan"


def test_editar_el_vehiculo_de_otro_taller_tampoco_se_puede(cliente, dueno, dueno_vecino):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    cliente_id = crear_cliente(cliente, token_propio)
    ajeno = crear_vehiculo(cliente, token_propio, cliente_id).json()["data"]["id"]

    respuesta = cliente.patch(
        f"/vehicles/{ajeno}",
        json={"brand": "Nissan"},
        headers=con_token(token_vecino),
    )

    assert respuesta.status_code == 404


def test_sin_token_no_se_puede_listar(cliente, dueno):
    respuesta = cliente.get("/vehicles")

    assert respuesta.status_code == 401

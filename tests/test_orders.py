"""Las ordenes de trabajo: lo que el taller tiene entre manos.

Una orden es un vehiculo de un cliente con un trabajo asociado y un estado. El estado
se mueve por su propio endpoint, no editando la ficha: mover el estado le avisa al
cliente, y eso no puede pasar de casualidad al corregir una falta de ortografia.
"""

from tests.conftest import con_token, crear_cliente_api, crear_vehiculo_api, entrar


def crear_orden(cliente, token, cliente_id, vehiculo_id, titulo="Revision de frenos", **extra):
    cuerpo = {"clientId": cliente_id, "vehicleId": vehiculo_id, "title": titulo}
    cuerpo.update(extra)
    return cliente.post("/orders", json=cuerpo, headers=con_token(token))


def taller_con_auto(cliente, token, patente="ABCD12", telefono="56911111111"):
    """Deja listo un cliente con su vehiculo y devuelve los dos ids."""
    cliente_id = crear_cliente_api(cliente, token, telefono=telefono)
    vehiculo_id = crear_vehiculo_api(cliente, token, cliente_id, patente=patente)
    return cliente_id, vehiculo_id


def test_una_orden_sin_avisos_no_trae_ninguno(cliente, dueno):
    """Recien creada no se le ha dicho nada al cliente todavia."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token)
    orden = crear_orden(cliente, token, cliente_id, vehiculo_id).json()["data"]["id"]

    respuesta = cliente.get(f"/orders/{orden}", headers=con_token(token))

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["latestNotification"] is None


def test_el_detalle_trae_el_aviso_pendiente(cliente, dueno):
    """Sin esto el frontend pierde el borrador al recargar la pagina.

    El aviso solo viaja en la respuesta del cambio de estado. Si el mecanico recarga,
    se queda sin el texto que tenia que mandar y sin el id para marcarlo como enviado.
    """
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token)
    orden = crear_orden(cliente, token, cliente_id, vehiculo_id).json()["data"]["id"]
    cambio = cliente.post(
        f"/orders/{orden}/status", json={"status": "listo"}, headers=con_token(token)
    ).json()["data"]["notification"]

    respuesta = cliente.get(f"/orders/{orden}", headers=con_token(token))

    aviso = respuesta.json()["data"]["latestNotification"]
    assert aviso["id"] == cambio["id"]
    assert aviso["message"] == cambio["message"]
    assert aviso["toPhone"] == cambio["toPhone"]


def test_el_detalle_trae_el_ultimo_aviso_no_el_primero(cliente, dueno):
    """La orden avanza varias veces; al mecanico le sirve el que tiene pendiente ahora."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token)
    orden = crear_orden(cliente, token, cliente_id, vehiculo_id).json()["data"]["id"]
    cliente.post(
        f"/orders/{orden}/status", json={"status": "en_reparacion"}, headers=con_token(token)
    )
    ultimo = cliente.post(
        f"/orders/{orden}/status", json={"status": "listo"}, headers=con_token(token)
    ).json()["data"]["notification"]

    respuesta = cliente.get(f"/orders/{orden}", headers=con_token(token))

    assert respuesta.json()["data"]["latestNotification"]["id"] == ultimo["id"]


def test_crear_una_orden_la_devuelve_con_su_id(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token)

    respuesta = crear_orden(cliente, token, cliente_id, vehiculo_id)

    assert respuesta.status_code == 201
    datos = respuesta.json()["data"]
    assert datos["id"]
    assert datos["title"] == "Revision de frenos"


def test_una_orden_nueva_empieza_recibida(cliente, dueno):
    """El auto acaba de entrar: ese es el estado, sin tener que declararlo."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token)

    respuesta = crear_orden(cliente, token, cliente_id, vehiculo_id)

    assert respuesta.json()["data"]["status"] == "recibido"


def test_un_estado_inventado_se_rechaza(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token)

    respuesta = crear_orden(cliente, token, cliente_id, vehiculo_id, status="lavandolo")

    assert respuesta.status_code == 422


def test_la_orden_trae_al_cliente_y_al_vehiculo_adentro(cliente, dueno):
    """Martin pinta la tarjeta con una sola llamada, sin ir a buscar cada pieza."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token, nombre="Juan Perez")
    vehiculo_id = crear_vehiculo_api(
        cliente, token, cliente_id, patente="ABCD12", marca="Toyota", modelo="Corolla"
    )

    datos = crear_orden(cliente, token, cliente_id, vehiculo_id).json()["data"]

    assert datos["client"]["name"] == "Juan Perez"
    assert datos["vehicle"]["plate"] == "ABCD12"
    assert datos["vehicleOrItem"] == "Toyota Corolla · Patente ABCD12"


def test_no_se_puede_abrir_una_orden_con_el_vehiculo_de_otro_taller(
    cliente, dueno, dueno_vecino
):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    cliente_ajeno, vehiculo_ajeno = taller_con_auto(cliente, token_propio)
    cliente_vecino = crear_cliente_api(cliente, token_vecino, telefono="56999999999")

    respuesta = crear_orden(cliente, token_vecino, cliente_vecino, vehiculo_ajeno)

    assert respuesta.status_code == 404


def test_el_vehiculo_tiene_que_ser_del_cliente_de_la_orden(cliente, dueno):
    """Elegir mal en la lista dejaria el aviso saliendo al telefono equivocado."""
    token = entrar(cliente, "dueno@taller.cl")
    _, vehiculo_de_juan = taller_con_auto(cliente, token)
    otro_cliente = crear_cliente_api(cliente, token, nombre="Maria Soto", telefono="56922222222")

    respuesta = crear_orden(cliente, token, otro_cliente, vehiculo_de_juan)

    assert respuesta.status_code == 400


def test_listar_devuelve_la_forma_de_lista_del_contrato(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token)
    crear_orden(cliente, token, cliente_id, vehiculo_id)

    respuesta = cliente.get("/orders", headers=con_token(token))

    assert respuesta.status_code == 200
    assert respuesta.json()["meta"] == {"page": 1, "limit": 20, "total": 1}


def test_las_ordenes_abiertas_dejan_fuera_las_entregadas(cliente, dueno):
    """El panel del mecanico muestra lo que tiene entre manos, no el archivo."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token)
    abierta = crear_orden(cliente, token, cliente_id, vehiculo_id, titulo="Frenos")
    otro_cliente, otro_vehiculo = taller_con_auto(
        cliente, token, patente="BBBB22", telefono="56922222222"
    )
    cerrada = crear_orden(cliente, token, otro_cliente, otro_vehiculo, titulo="Aceite")
    cliente.post(
        f"/orders/{cerrada.json()['data']['id']}/status",
        json={"status": "entregado"},
        headers=con_token(token),
    )

    respuesta = cliente.get("/orders", params={"open": True}, headers=con_token(token))

    assert [o["id"] for o in respuesta.json()["data"]] == [abierta.json()["data"]["id"]]


def test_un_taller_no_ve_las_ordenes_del_otro(cliente, dueno, dueno_vecino):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token_propio)
    crear_orden(cliente, token_propio, cliente_id, vehiculo_id)

    respuesta = cliente.get("/orders", headers=con_token(token_vecino))

    assert respuesta.json()["data"] == []


def test_pedir_la_orden_de_otro_taller_responde_no_encontrado(cliente, dueno, dueno_vecino):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token_propio)
    ajena = crear_orden(cliente, token_propio, cliente_id, vehiculo_id).json()["data"]["id"]

    respuesta = cliente.get(f"/orders/{ajena}", headers=con_token(token_vecino))

    assert respuesta.status_code == 404


def test_editar_la_orden_cambia_el_texto(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token)
    orden = crear_orden(cliente, token, cliente_id, vehiculo_id).json()["data"]["id"]

    respuesta = cliente.patch(
        f"/orders/{orden}",
        json={"description": "Pastillas delanteras y liquido"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["description"] == "Pastillas delanteras y liquido"


def test_editar_la_orden_no_puede_mover_el_estado(cliente, dueno):
    """Mover el estado le escribe al cliente. No puede pasar corrigiendo una palabra."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token)
    orden = crear_orden(cliente, token, cliente_id, vehiculo_id).json()["data"]["id"]

    respuesta = cliente.patch(
        f"/orders/{orden}",
        json={"title": "Frenos", "status": "entregado"},
        headers=con_token(token),
    )

    assert respuesta.json()["data"]["status"] == "recibido"


def test_editar_la_orden_de_otro_taller_tampoco_se_puede(cliente, dueno, dueno_vecino):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token_propio)
    ajena = crear_orden(cliente, token_propio, cliente_id, vehiculo_id).json()["data"]["id"]

    respuesta = cliente.patch(
        f"/orders/{ajena}", json={"title": "Otra cosa"}, headers=con_token(token_vecino)
    )

    assert respuesta.status_code == 404


def test_sin_token_no_se_puede_listar(cliente, dueno):
    respuesta = cliente.get("/orders")

    assert respuesta.status_code == 401


def test_el_historial_del_vehiculo_muestra_sus_ordenes(cliente, dueno):
    """La pregunta de siempre: que le hemos hecho antes a este auto."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token)
    crear_orden(cliente, token, cliente_id, vehiculo_id, titulo="Frenos")
    crear_orden(cliente, token, cliente_id, vehiculo_id, titulo="Cambio de aceite")

    respuesta = cliente.get(f"/vehicles/{vehiculo_id}/history", headers=con_token(token))

    assert respuesta.status_code == 200
    assert sorted(o["title"] for o in respuesta.json()["data"]) == [
        "Cambio de aceite",
        "Frenos",
    ]

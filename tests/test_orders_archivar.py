"""Archivar una orden de trabajo.

Mismo criterio que con el cliente: `DELETE /orders/:id` la saca del tablero pero no la
borra de la tabla. Los avisos que ya se le mandaron al cliente cuelgan de la orden, y
una orden entregada es la boleta de lo que se cobro.
"""

from tests.conftest import con_token, crear_cliente_api, crear_vehiculo_api, entrar
from tests.test_orders import crear_orden, taller_con_auto


def archivar(cliente, token, orden_id):
    return cliente.delete(f"/orders/{orden_id}", headers=con_token(token))


def orden_lista(cliente, token, patente="ABCD12", telefono="56911111111"):
    cliente_id, vehiculo_id = taller_con_auto(cliente, token, patente=patente, telefono=telefono)
    orden_id = crear_orden(cliente, token, cliente_id, vehiculo_id).json()["data"]["id"]
    return cliente_id, vehiculo_id, orden_id


def test_archivar_una_orden_responde_sin_contenido(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    _, _, orden_id = orden_lista(cliente, token)

    respuesta = archivar(cliente, token, orden_id)

    assert respuesta.status_code == 204
    assert respuesta.content == b""


def test_la_orden_archivada_no_sale_en_el_tablero(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    _, _, orden_id = orden_lista(cliente, token)

    archivar(cliente, token, orden_id)

    cuerpo = cliente.get("/orders", headers=con_token(token)).json()
    assert cuerpo["data"] == []
    assert cuerpo["meta"]["total"] == 0


def test_la_orden_archivada_tampoco_sale_entre_las_abiertas(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    _, _, orden_id = orden_lista(cliente, token)

    archivar(cliente, token, orden_id)

    assert cliente.get("/orders?open=true", headers=con_token(token)).json()["data"] == []


def test_pedir_una_orden_archivada_responde_no_encontrada(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    _, _, orden_id = orden_lista(cliente, token)
    archivar(cliente, token, orden_id)

    assert cliente.get(f"/orders/{orden_id}", headers=con_token(token)).status_code == 404


def test_editar_una_orden_archivada_responde_no_encontrada(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    _, _, orden_id = orden_lista(cliente, token)
    archivar(cliente, token, orden_id)

    respuesta = cliente.patch(
        f"/orders/{orden_id}",
        json={"title": "Otra cosa"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 404


def test_mover_de_estado_una_orden_archivada_no_le_avisa_a_nadie(cliente, dueno):
    """Lo importante no es el 404: es que no salga un WhatsApp de una orden archivada."""
    token = entrar(cliente, "dueno@taller.cl")
    _, _, orden_id = orden_lista(cliente, token)
    archivar(cliente, token, orden_id)

    respuesta = cliente.post(
        f"/orders/{orden_id}/status",
        json={"status": "listo"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 404


def test_archivar_dos_veces_responde_no_encontrada(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    _, _, orden_id = orden_lista(cliente, token)
    archivar(cliente, token, orden_id)

    assert archivar(cliente, token, orden_id).status_code == 404


def test_archivar_la_orden_de_otro_taller_no_se_puede(cliente, dueno, dueno_vecino):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    _, _, orden_id = orden_lista(cliente, token_propio)

    assert archivar(cliente, token_vecino, orden_id).status_code == 404
    assert cliente.get(f"/orders/{orden_id}", headers=con_token(token_propio)).status_code == 200


def test_sin_token_no_se_puede_archivar(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    _, _, orden_id = orden_lista(cliente, token)

    assert cliente.delete(f"/orders/{orden_id}").status_code == 401


def test_la_orden_archivada_no_sale_en_el_historial_del_vehiculo(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    _, vehiculo_id, orden_id = orden_lista(cliente, token)

    archivar(cliente, token, orden_id)

    cuerpo = cliente.get(f"/vehicles/{vehiculo_id}/history", headers=con_token(token)).json()
    assert cuerpo["data"] == []
    assert cuerpo["meta"]["total"] == 0


def test_archivar_una_orden_no_toca_a_las_demas(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, vehiculo_id = taller_con_auto(cliente, token)
    archivada = crear_orden(cliente, token, cliente_id, vehiculo_id, titulo="Se va").json()["data"]["id"]
    crear_orden(cliente, token, cliente_id, vehiculo_id, titulo="Se queda")

    archivar(cliente, token, archivada)

    cuerpo = cliente.get("/orders", headers=con_token(token)).json()
    assert [o["title"] for o in cuerpo["data"]] == ["Se queda"]
    assert cuerpo["meta"]["total"] == 1


def test_archivar_la_orden_libera_al_cliente_para_archivarlo(cliente, dueno):
    """La orden abierta era lo unico que frenaba el archivo de la ficha."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id, _, orden_id = orden_lista(cliente, token)
    assert cliente.delete(f"/clients/{cliente_id}", headers=con_token(token)).status_code == 409

    archivar(cliente, token, orden_id)

    assert cliente.delete(f"/clients/{cliente_id}", headers=con_token(token)).status_code == 204


def test_buscar_por_patente_no_devuelve_la_archivada(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    _, _, orden_id = orden_lista(cliente, token, patente="ABCD12")

    archivar(cliente, token, orden_id)

    respuesta = cliente.get("/orders?search=ABCD12", headers=con_token(token))
    assert respuesta.json()["data"] == []

"""Archivar la ficha de un cliente.

Borrar de verdad no es opcion: el cliente cuelga de sus vehiculos, sus ordenes y sus
avisos, y sacarlo de la tabla le partiria el historial al taller. `DELETE /clients/:id`
lo archiva: desaparece de las listas, pero las ordenes que ya pasaron quedan enteras.
"""

from tests.conftest import con_token, crear_cliente_api, crear_vehiculo_api, entrar
from tests.test_orders import crear_orden


def archivar(cliente, token, cliente_id):
    return cliente.delete(f"/clients/{cliente_id}", headers=con_token(token))


def test_archivar_un_cliente_responde_sin_contenido(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token)

    respuesta = archivar(cliente, token, cliente_id)

    assert respuesta.status_code == 204
    assert respuesta.content == b""


def test_el_cliente_archivado_no_sale_en_el_listado(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token)

    archivar(cliente, token, cliente_id)

    cuerpo = cliente.get("/clients", headers=con_token(token)).json()
    assert cuerpo["data"] == []
    assert cuerpo["meta"]["total"] == 0


def test_pedir_un_cliente_archivado_responde_no_encontrado(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token)
    archivar(cliente, token, cliente_id)

    respuesta = cliente.get(f"/clients/{cliente_id}", headers=con_token(token))

    assert respuesta.status_code == 404


def test_editar_un_cliente_archivado_responde_no_encontrado(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token)
    archivar(cliente, token, cliente_id)

    respuesta = cliente.patch(
        f"/clients/{cliente_id}",
        json={"name": "Otro Nombre"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 404


def test_archivar_dos_veces_responde_no_encontrado(cliente, dueno):
    """La segunda vez ya no hay nada que archivar."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token)
    archivar(cliente, token, cliente_id)

    assert archivar(cliente, token, cliente_id).status_code == 404


def test_archivar_el_cliente_de_otro_taller_no_se_puede(cliente, dueno, dueno_vecino):
    """404 y no 403: por el mismo criterio del resto del modulo."""
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    cliente_id = crear_cliente_api(cliente, token_propio)

    assert archivar(cliente, token_vecino, cliente_id).status_code == 404
    # Y sigue en pie para su taller.
    assert cliente.get(f"/clients/{cliente_id}", headers=con_token(token_propio)).status_code == 200


def test_sin_token_no_se_puede_archivar(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token)

    assert cliente.delete(f"/clients/{cliente_id}").status_code == 401


def test_un_cliente_con_una_orden_abierta_no_se_archiva(cliente, dueno):
    """El auto esta en el taller ahora mismo: archivarlo es casi seguro un error."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token)
    vehiculo_id = crear_vehiculo_api(cliente, token, cliente_id)
    crear_orden(cliente, token, cliente_id, vehiculo_id)

    respuesta = archivar(cliente, token, cliente_id)

    assert respuesta.status_code == 409
    assert "abierta" in respuesta.json()["error"]["message"].lower()


def test_un_cliente_con_la_orden_ya_entregada_si_se_archiva(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token)
    vehiculo_id = crear_vehiculo_api(cliente, token, cliente_id)
    orden_id = crear_orden(cliente, token, cliente_id, vehiculo_id).json()["data"]["id"]
    cliente.post(
        f"/orders/{orden_id}/status",
        json={"status": "entregado"},
        headers=con_token(token),
    )

    assert archivar(cliente, token, cliente_id).status_code == 204


def test_archivar_al_cliente_no_borra_su_historial(cliente, dueno):
    """Lo que se archiva es la ficha, no lo que se le hizo al auto."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token)
    vehiculo_id = crear_vehiculo_api(cliente, token, cliente_id)
    orden_id = crear_orden(cliente, token, cliente_id, vehiculo_id).json()["data"]["id"]
    cliente.post(
        f"/orders/{orden_id}/status",
        json={"status": "entregado"},
        headers=con_token(token),
    )

    archivar(cliente, token, cliente_id)

    respuesta = cliente.get(f"/orders/{orden_id}", headers=con_token(token))
    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["id"] == orden_id


def test_no_se_le_puede_hacer_una_orden_nueva_a_un_cliente_archivado(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token)
    vehiculo_id = crear_vehiculo_api(cliente, token, cliente_id)
    archivar(cliente, token, cliente_id)

    respuesta = crear_orden(cliente, token, cliente_id, vehiculo_id)

    assert respuesta.status_code == 404


def test_no_se_le_puede_colgar_un_vehiculo_a_un_cliente_archivado(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token)
    archivar(cliente, token, cliente_id)

    respuesta = cliente.post(
        "/vehicles",
        json={"clientId": cliente_id, "plate": "XYZW99"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 404


def test_los_vehiculos_del_cliente_archivado_no_salen_en_el_listado(cliente, dueno):
    """Si siguieran saliendo, buscar la patente llevaria a una ficha que ya no esta."""
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token)
    crear_vehiculo_api(cliente, token, cliente_id, patente="ABCD12")

    archivar(cliente, token, cliente_id)

    cuerpo = cliente.get("/vehicles", headers=con_token(token)).json()
    assert cuerpo["data"] == []
    assert cuerpo["meta"]["total"] == 0
    assert cliente.get("/vehicles?plate=ABCD12", headers=con_token(token)).json()["data"] == []


def test_dar_de_alta_otra_vez_el_mismo_telefono_revive_la_ficha(cliente, dueno):
    """El telefono es unico por taller: sin esto, archivar dejaria ese numero inservible.

    Y revivir la ficha de siempre es lo que el taller espera: el cliente que vuelve trae
    consigo el historial de su auto.
    """
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token, nombre="Juan Perez", telefono="56911111111")
    archivar(cliente, token, cliente_id)

    respuesta = cliente.post(
        "/clients",
        json={"name": "Juan Perez Soto", "phone": "56911111111"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 201
    datos = respuesta.json()["data"]
    assert datos["id"] == cliente_id, "deberia ser la misma ficha, no una nueva"
    assert datos["name"] == "Juan Perez Soto", "y con los datos que trajo ahora"
    assert cliente.get(f"/clients/{cliente_id}", headers=con_token(token)).status_code == 200


def test_revivir_la_ficha_devuelve_sus_vehiculos(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    cliente_id = crear_cliente_api(cliente, token, telefono="56911111111")
    crear_vehiculo_api(cliente, token, cliente_id, patente="ABCD12")
    archivar(cliente, token, cliente_id)

    cliente.post(
        "/clients",
        json={"name": "Juan Perez", "phone": "56911111111"},
        headers=con_token(token),
    )

    patentes = [v["plate"] for v in cliente.get("/vehicles", headers=con_token(token)).json()["data"]]
    assert patentes == ["ABCD12"]


def test_el_telefono_repetido_de_un_cliente_vivo_se_sigue_rechazando(cliente, dueno):
    """Revivir es solo para el archivado: dos fichas vivas iguales siguen sin permitirse."""
    token = entrar(cliente, "dueno@taller.cl")
    crear_cliente_api(cliente, token, telefono="56911111111")

    respuesta = cliente.post(
        "/clients",
        json={"name": "Otro Juan", "phone": "56911111111"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 409


def test_archivar_a_uno_no_toca_al_resto(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    archivado = crear_cliente_api(cliente, token, nombre="Se Va", telefono="56911111111")
    crear_cliente_api(cliente, token, nombre="Se Queda", telefono="56922222222")

    archivar(cliente, token, archivado)

    cuerpo = cliente.get("/clients", headers=con_token(token)).json()
    assert [c["name"] for c in cuerpo["data"]] == ["Se Queda"]
    assert cuerpo["meta"]["total"] == 1

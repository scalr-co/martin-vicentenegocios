"""Llevarse los datos del taller en un archivo, que es la otra ventaja del plan Plus.

Un taller que puede exportar sus clientes no esta atrapado, y eso es parte de lo que se
vende: los datos son suyos. El archivo lo va a abrir en Excel el dueno de un taller en
Chile, asi que las dos decisiones que se prueban aca -el separador y el BOM- no son
detalles: sin ellas el archivo se ve como una sola columna con los acentos rotos.
"""

from tests.conftest import con_token, crear_cliente_api, crear_vehiculo_api, entrar
from tests.test_admin import alta_de_taller
from tests.test_admin import clave_de_admin_configurada  # noqa: F401  (fixture autouse)
from tests.test_admin import token_admin  # noqa: F401  (fixture)
from tests.test_reportes import _taller_plus

CLAVE_DEL_DUENO = "una-clave-larga-de-verdad"


def _con_una_orden(cliente, token, nombre="Juan Perez", patente="ABCD12", titulo="Frenos"):
    cliente_id = crear_cliente_api(cliente, token, nombre=nombre, telefono="56911111111")
    vehiculo_id = crear_vehiculo_api(
        cliente, token, cliente_id, patente=patente, marca="Toyota", modelo="RAV4"
    )
    respuesta = cliente.post(
        "/orders",
        json={"clientId": cliente_id, "vehicleId": vehiculo_id, "title": titulo},
        headers=con_token(token),
    )
    assert respuesta.status_code == 201, respuesta.text
    return cliente_id


def test_el_archivo_de_clientes_trae_a_los_clientes_del_taller(cliente, token_admin):
    token = _taller_plus(cliente, token_admin)
    _con_una_orden(cliente, token, nombre="Juan Perez")

    respuesta = cliente.get("/exports/clients", headers=con_token(token))

    assert respuesta.status_code == 200, respuesta.text
    texto = respuesta.text
    assert "Nombre" in texto
    assert "Juan Perez" in texto
    assert "56911111111" in texto


def test_el_archivo_llega_con_nombre_para_guardar(cliente, token_admin):
    """Sin Content-Disposition el navegador lo abre en una pestana en vez de bajarlo."""
    token = _taller_plus(cliente, token_admin)

    respuesta = cliente.get("/exports/clients", headers=con_token(token))

    assert "text/csv" in respuesta.headers["content-type"]
    assert "clientes.csv" in respuesta.headers["content-disposition"]


def test_el_archivo_se_abre_bien_en_excel_chileno(cliente, token_admin):
    """Dos decisiones que se ven a simple vista al abrirlo.

    El separador es punto y coma porque en la configuracion regional chilena la coma es el
    separador decimal: con comas, Excel mete todo en una sola columna. Y el archivo parte
    con BOM, o los acentos y las enes salen rotos.
    """
    token = _taller_plus(cliente, token_admin)
    _con_una_orden(cliente, token, nombre="Ramon Nunez")

    texto = cliente.get("/exports/clients", headers=con_token(token)).text

    assert texto.startswith("﻿")
    assert ";" in texto.splitlines()[0]
    assert "," not in texto.splitlines()[0]


def test_el_historial_trae_una_fila_por_orden_con_su_auto(cliente, token_admin):
    token = _taller_plus(cliente, token_admin)
    _con_una_orden(cliente, token, patente="ABCD12", titulo="Cambio de frenos")

    respuesta = cliente.get("/exports/history", headers=con_token(token))

    assert respuesta.status_code == 200, respuesta.text
    assert "historial.csv" in respuesta.headers["content-disposition"]
    filas = [f for f in respuesta.text.splitlines() if f.strip()]
    assert len(filas) == 2  # el encabezado y la orden
    assert "ABCD12" in filas[1]
    assert "Cambio de frenos" in filas[1]
    assert "Juan Perez" in filas[1]


def test_el_taller_de_al_lado_no_viaja_en_el_archivo(cliente, token_admin):
    """Si el aislamiento se respeta en la pantalla pero no en el archivo, no se respeta."""
    token = _taller_plus(cliente, token_admin)
    _con_una_orden(cliente, token, nombre="Cliente Propio", patente="AAAA11")

    token_vecino = _taller_plus(
        cliente, token_admin, email="otro@vecino.cl", workshopName="Taller Vecino"
    )
    _con_una_orden(cliente, token_vecino, nombre="Cliente Ajeno", patente="BBBB22")

    clientes = cliente.get("/exports/clients", headers=con_token(token)).text
    historial = cliente.get("/exports/history", headers=con_token(token)).text

    assert "Cliente Propio" in clientes
    assert "Cliente Ajeno" not in clientes
    assert "AAAA11" in historial
    assert "BBBB22" not in historial


def test_el_plan_basico_no_exporta(cliente, token_admin):
    assert alta_de_taller(cliente, token_admin).status_code == 201
    token = entrar(cliente, "marcela@sancristobal.cl", clave=CLAVE_DEL_DUENO)

    assert cliente.get("/exports/clients", headers=con_token(token)).status_code == 403
    assert cliente.get("/exports/history", headers=con_token(token)).status_code == 403


def test_sin_sesion_no_se_baja_nada(cliente):
    assert cliente.get("/exports/clients").status_code == 401
    assert cliente.get("/exports/history").status_code == 401

"""Mirar hacia adentro de un taller, desde el panel de Solve.

Existe por una pregunta que hoy no se puede contestar: el taller escribe "no me llego el
aviso al cliente" y no hay forma de mirar. Antes de esto, un admin de plataforma no veia
nada de ningun taller, y la unica salida era pedirle capturas de pantalla al dueno.

Dos reglas sostienen todo lo de aca:
- **Es una puerta aparte.** Los endpoints del taller (`/orders`, `/clients`, `/vehicles`)
  siguen filtrando por el taller del token, sin excepcion. Solve no entra por ahi: entra
  por `/admin/workshops/:id/...`, que pide rol de plataforma.
- **Se mira, no se toca.** Por esta puerta no se mueve una orden ni se corrige una ficha.
  Para eso estan las acciones del panel, que ya quedan anotadas.
"""

from datetime import timedelta

from sqlalchemy import select

from app.models import ACCION_TALLER_MIRADO, AdminAudit, User
from app.models.base import ahora
from tests.conftest import (
    con_token,
    crear_cliente_api,
    crear_vehiculo_api,
    entrar,
)
from tests.test_admin import alta_de_taller  # noqa: F401  (usa el mismo cuerpo de alta)
from tests.test_admin import clave_de_admin_configurada  # noqa: F401  (fixture autouse)
from tests.test_admin import token_admin  # noqa: F401  (fixture)

CLAVE_DEL_DUENO = "una-clave-larga-de-verdad"


def _taller_con_una_orden(cliente, token_admin, titulo="Frenos", patente="ABCD12", alta=None):
    """Un taller de verdad: su dueno, su cliente, su auto y una orden abierta.

    Se arma todo por la API y con el token del dueno, como pasaria en el taller. Meter
    las filas a mano en la base saltaria justo lo que hay que comprobar: que Solve ve lo
    que el taller escribio, no lo que el test invento.

    `alta` cambia los datos del taller, para poder levantar un segundo y comprobar que
    uno no ve lo del otro.
    """
    alta = alta or {}
    correo = alta.get("email", "marcela@sancristobal.cl")

    taller_id = alta_de_taller(cliente, token_admin, **alta).json()["data"]["workshop"]["id"]
    token_dueno = entrar(cliente, correo, clave=CLAVE_DEL_DUENO)

    cliente_id = crear_cliente_api(cliente, token_dueno)
    vehiculo_id = crear_vehiculo_api(cliente, token_dueno, cliente_id, patente=patente)
    orden = cliente.post(
        "/orders",
        json={"clientId": cliente_id, "vehicleId": vehiculo_id, "title": titulo},
        headers=con_token(token_dueno),
    )
    assert orden.status_code == 201, orden.text

    return taller_id, token_dueno, orden.json()["data"]["id"]


def test_solve_ve_las_ordenes_de_un_taller_que_no_es_suyo(cliente, token_admin):
    """Lo que se mira cuando el taller llama: que tiene entre manos ahora mismo."""
    taller_id, _, orden_id = _taller_con_una_orden(cliente, token_admin)

    respuesta = cliente.get(
        f"/admin/workshops/{taller_id}/orders", headers=con_token(token_admin)
    )

    assert respuesta.status_code == 200, respuesta.text
    ordenes = respuesta.json()["data"]
    assert [orden["id"] for orden in ordenes] == [orden_id]
    assert ordenes[0]["title"] == "Frenos"


def test_la_orden_trae_el_telefono_del_cliente(cliente, token_admin):
    """Se ve el numero completo, y es la razon de ser de esto.

    El problema tipico es "el aviso le llego a otra persona". Con el telefono tapado no
    se puede diagnosticar: hay que ver a que numero salio.
    """
    taller_id, _, _ = _taller_con_una_orden(cliente, token_admin)

    respuesta = cliente.get(
        f"/admin/workshops/{taller_id}/orders", headers=con_token(token_admin)
    )

    primera = respuesta.json()["data"][0]
    assert primera["client"]["phone"] == "56911111111"
    assert primera["client"]["name"] == "Juan Perez"


def test_la_ficha_dice_como_le_esta_yendo_al_taller(cliente, token_admin):
    """Los cinco numeros que se miran antes de entrar a revisar orden por orden."""
    taller_id, token_dueno, orden_id = _taller_con_una_orden(cliente, token_admin)
    cliente.post(
        f"/orders/{orden_id}/status",
        json={"status": "listo"},
        headers=con_token(token_dueno),
    )

    respuesta = cliente.get(
        f"/admin/workshops/{taller_id}", headers=con_token(token_admin)
    )

    assert respuesta.status_code == 200, respuesta.text
    ficha = respuesta.json()["data"]
    assert ficha["name"] == "Taller San Cristobal"
    assert ficha["stats"] == {
        "ordersTotal": 1,
        "ordersOpen": 1,
        "lastActivityAt": ficha["stats"]["lastActivityAt"],
        "noticesPending": 1,
        "usersActive": 1,
    }
    assert ficha["stats"]["lastActivityAt"].endswith("Z")


def test_el_aviso_que_si_se_envio_deja_de_contar_como_pendiente(cliente, token_admin):
    """`noticesPending` es la senal de "mueve ordenes pero no avisa a nadie".

    Si contara todos los avisos, un taller que hace su pega perfecta se veria igual de
    mal que uno que no le escribe a ningun cliente.
    """
    taller_id, token_dueno, orden_id = _taller_con_una_orden(cliente, token_admin)
    aviso = cliente.post(
        f"/orders/{orden_id}/status",
        json={"status": "listo"},
        headers=con_token(token_dueno),
    ).json()["data"]["notification"]
    cliente.post(f"/notifications/{aviso['id']}/sent", headers=con_token(token_dueno))

    ficha = cliente.get(
        f"/admin/workshops/{taller_id}", headers=con_token(token_admin)
    ).json()["data"]

    assert ficha["stats"]["noticesPending"] == 0


def test_un_taller_recien_creado_no_rompe_la_ficha(cliente, token_admin):
    """Sin ordenes no hay ultima actividad, y eso es un dato, no un error."""
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]

    ficha = cliente.get(
        f"/admin/workshops/{taller_id}", headers=con_token(token_admin)
    ).json()["data"]

    assert ficha["stats"]["lastActivityAt"] is None
    assert ficha["stats"]["ordersTotal"] == 0
    assert ficha["stats"]["usersActive"] == 1


def test_un_taller_dado_de_baja_se_puede_seguir_mirando(cliente, token_admin):
    """Cuando un taller se va, lo que uno quiere es entender por que."""
    taller_id, _, _ = _taller_con_una_orden(cliente, token_admin)
    cliente.delete(f"/admin/workshops/{taller_id}", headers=con_token(token_admin))

    ficha = cliente.get(f"/admin/workshops/{taller_id}", headers=con_token(token_admin))
    ordenes = cliente.get(
        f"/admin/workshops/{taller_id}/orders", headers=con_token(token_admin)
    )

    assert ficha.status_code == 200
    assert ficha.json()["data"]["deletedAt"] is not None
    assert len(ordenes.json()["data"]) == 1


def test_el_taller_interno_de_solve_no_se_mira(cliente, token_admin, sesion):
    """El taller donde viven las cuentas de admin no es un taller mecanico.

    No sale en la lista del panel, y por la misma razon tampoco se abre su ficha: si se
    abriera, el panel mostraria un taller que nadie puede administrar ni suspender.
    """
    from app.models import Workshop

    interno = sesion.scalar(select(Workshop).where(Workshop.internal.is_(True)))

    respuesta = cliente.get(
        f"/admin/workshops/{interno.id}", headers=con_token(token_admin)
    )

    assert respuesta.status_code == 404


def test_el_dueno_de_un_taller_no_entra_por_esta_puerta(cliente, token_admin):
    """Ni al suyo. Administrar el propio taller no es administrar la plataforma, y esta
    puerta no filtra por el token: si se abriera, bastaria cambiar el id de la URL."""
    taller_id, token_dueno, _ = _taller_con_una_orden(cliente, token_admin)

    respuesta = cliente.get(
        f"/admin/workshops/{taller_id}/orders", headers=con_token(token_dueno)
    )

    assert respuesta.status_code == 403


def test_el_mecanico_tampoco(cliente, token_admin, sesion):
    taller_id, token_dueno, _ = _taller_con_una_orden(cliente, token_admin)
    cliente.post(
        "/users",
        json={"name": "Pedro", "email": "pedro@sancristobal.cl", "password": "clave-larga-suya"},
        headers=con_token(token_dueno),
    )
    token_mecanico = entrar(cliente, "pedro@sancristobal.cl", clave="clave-larga-suya")

    respuesta = cliente.get(
        f"/admin/workshops/{taller_id}/orders", headers=con_token(token_mecanico)
    )

    assert respuesta.status_code == 403


def test_sin_sesion_no_se_mira_nada(cliente, token_admin):
    taller_id, _, _ = _taller_con_una_orden(cliente, token_admin)

    respuesta = cliente.get(f"/admin/workshops/{taller_id}/orders")

    assert respuesta.status_code == 401


def test_los_endpoints_del_taller_siguen_filtrando_por_el_token(cliente, token_admin):
    """La invariante de siempre, que esta puerta no cambia.

    Solve ve las ordenes de un taller por `/admin/workshops/:id/orders` y por ningun otro
    lado. Pedir `/orders` con un token de plataforma sigue devolviendo la lista vacia,
    porque el taller del admin es el interno de Solve y ahi no hay ordenes.
    """
    _taller_con_una_orden(cliente, token_admin)

    respuesta = cliente.get("/orders", headers=con_token(token_admin))

    assert respuesta.status_code == 200
    assert respuesta.json()["data"] == []


def test_por_esta_puerta_no_se_escribe(cliente, token_admin):
    """Solo lectura, y comprobado. Si manana alguien cuelga un POST aca, este test cae.

    El 405 dice "esa direccion existe, pero no para eso": es la respuesta de una ruta que
    solo tiene GET. Mover el estado ni siquiera tiene direccion, y por eso da 404.
    """
    taller_id, _, orden_id = _taller_con_una_orden(cliente, token_admin)
    direccion = f"/admin/workshops/{taller_id}/orders/{orden_id}"

    editar = cliente.patch(
        direccion, json={"title": "Otra cosa"}, headers=con_token(token_admin)
    )
    archivar = cliente.delete(direccion, headers=con_token(token_admin))
    mover = cliente.post(
        f"{direccion}/status", json={"status": "listo"}, headers=con_token(token_admin)
    )

    assert editar.status_code == 405
    assert archivar.status_code == 405
    assert mover.status_code == 404


def test_un_taller_que_no_existe_da_404(cliente, token_admin):
    respuesta = cliente.get(
        "/admin/workshops/no-existe/orders", headers=con_token(token_admin)
    )

    assert respuesta.status_code == 404


def test_los_filtros_son_los_mismos_que_ve_el_taller(cliente, token_admin):
    """`?open=` y `?status=` filtran igual, y el total cuenta lo filtrado y no el resto."""
    taller_id, token_dueno, orden_id = _taller_con_una_orden(cliente, token_admin)
    cliente.post(
        f"/orders/{orden_id}/status",
        json={"status": "entregado"},
        headers=con_token(token_dueno),
    )

    abiertas = cliente.get(
        f"/admin/workshops/{taller_id}/orders?open=true", headers=con_token(token_admin)
    )
    entregadas = cliente.get(
        f"/admin/workshops/{taller_id}/orders?status=entregado",
        headers=con_token(token_admin),
    )

    assert abiertas.json()["data"] == []
    assert abiertas.json()["meta"]["total"] == 0
    assert [orden["id"] for orden in entregadas.json()["data"]] == [orden_id]


def test_se_busca_por_patente_igual_que_en_el_panel(cliente, token_admin):
    """Es lo primero que se hace por telefono: "dame la patente" y buscarla."""
    taller_id, token_dueno, orden_id = _taller_con_una_orden(cliente, token_admin)

    encontrada = cliente.get(
        f"/admin/workshops/{taller_id}/orders?search=abcd", headers=con_token(token_admin)
    )
    otra = cliente.get(
        f"/admin/workshops/{taller_id}/orders?search=zzzz", headers=con_token(token_admin)
    )

    assert [orden["id"] for orden in encontrada.json()["data"]] == [orden_id]
    assert otra.json()["data"] == []


def test_el_detalle_dice_quien_movio_la_orden_y_cuando(cliente, token_admin):
    """La pregunta que aparece cuando algo sale mal: quien la dio por lista.

    El nombre viene resuelto y no el id: quien mira desde el panel no tiene forma de
    saber a quien corresponde un uuid del taller de otro.
    """
    taller_id, token_dueno, orden_id = _taller_con_una_orden(cliente, token_admin)
    cliente.post(
        f"/orders/{orden_id}/status",
        json={"status": "en_reparacion"},
        headers=con_token(token_dueno),
    )

    respuesta = cliente.get(
        f"/admin/workshops/{taller_id}/orders/{orden_id}", headers=con_token(token_admin)
    )

    assert respuesta.status_code == 200, respuesta.text
    eventos = respuesta.json()["data"]["events"]
    assert len(eventos) == 1
    assert eventos[0]["fromStatus"] == "recibido"
    assert eventos[0]["toStatus"] == "en_reparacion"
    assert eventos[0]["userName"] == "Marcela"
    assert eventos[0]["createdAt"]


def test_el_detalle_trae_todos_los_avisos_y_no_solo_el_ultimo(cliente, token_admin):
    """Se mira para responder "el WhatsApp salio o quedo a medias".

    El panel del taller muestra solo el ultimo aviso, que es lo que necesita para abrir
    wa.me. Para ayudar hace falta la tira completa: cuales llegaron a `sent` y cuales
    quedaron en `link_ready` porque nadie apreto enviar.
    """
    taller_id, token_dueno, orden_id = _taller_con_una_orden(cliente, token_admin)
    for estado in ("en_reparacion", "listo"):
        cliente.post(
            f"/orders/{orden_id}/status",
            json={"status": estado},
            headers=con_token(token_dueno),
        )

    respuesta = cliente.get(
        f"/admin/workshops/{taller_id}/orders/{orden_id}", headers=con_token(token_admin)
    )

    avisos = respuesta.json()["data"]["notifications"]
    assert len(avisos) == 2
    assert [aviso["status"] for aviso in avisos] == ["link_ready", "link_ready"]
    assert avisos[0]["toPhone"] == "56911111111"


def test_una_orden_de_otro_taller_no_se_cuela_por_el_id(cliente, token_admin):
    """El id de la URL manda de que taller se trata, asi que hay que comprobar los dos.

    404 y no 403, igual que en el resto del sistema: un 403 confirmaria que ese id existe.
    """
    taller_id, _, _ = _taller_con_una_orden(cliente, token_admin)
    _, _, orden_ajena = _taller_con_una_orden(
        cliente,
        token_admin,
        alta={"email": "otro@vecino.cl", "workshopName": "Taller El Vecino"},
        patente="WXYZ99",
    )

    respuesta = cliente.get(
        f"/admin/workshops/{taller_id}/orders/{orden_ajena}",
        headers=con_token(token_admin),
    )

    assert respuesta.status_code == 404


def test_un_estado_inventado_lo_dice_en_vez_de_devolver_vacio(cliente, token_admin):
    taller_id, _, _ = _taller_con_una_orden(cliente, token_admin)

    respuesta = cliente.get(
        f"/admin/workshops/{taller_id}/orders?status=inventado",
        headers=con_token(token_admin),
    )

    assert respuesta.status_code == 422


def _visitas(sesion, taller_id: str):
    return sesion.scalars(
        select(AdminAudit).where(
            AdminAudit.action == ACCION_TALLER_MIRADO,
            AdminAudit.workshop_id == taller_id,
        )
    ).all()


def test_entrar_a_mirar_un_taller_queda_anotado(cliente, token_admin, sesion):
    """Mirar los datos de un taller no es gratis: hay que poder decir quien entro.

    Es la misma razon por la que se anota el cambio de clave del dueno. Con tres personas
    con acceso al panel, "alguien entro a ver las ordenes de Marbella" tiene que tener un
    nombre al lado.
    """
    taller_id, _, _ = _taller_con_una_orden(cliente, token_admin)
    admin = sesion.scalar(select(User).where(User.email == "vicente@solve.cl"))

    cliente.get(f"/admin/workshops/{taller_id}", headers=con_token(token_admin))

    visitas = _visitas(sesion, taller_id)
    assert len(visitas) == 1
    assert visitas[0].actor_user_id == admin.id


def test_recargar_la_ficha_no_llena_el_registro_de_ruido(cliente, token_admin, sesion):
    """Interesa "Vicente entro a mirar Marbella el martes", no cuantas veces recargo.

    Sin esta ventana, revisar un taller un rato deja veinte filas identicas y el registro
    se vuelve ilegible justo cuando hay que leerlo.
    """
    taller_id, _, _ = _taller_con_una_orden(cliente, token_admin)

    for _ in range(3):
        cliente.get(f"/admin/workshops/{taller_id}", headers=con_token(token_admin))

    assert len(_visitas(sesion, taller_id)) == 1


def test_volver_al_dia_siguiente_si_queda_anotado(cliente, token_admin, sesion):
    """La ventana agrupa una sesion de soporte, no esconde las visitas siguientes."""
    taller_id, _, _ = _taller_con_una_orden(cliente, token_admin)
    cliente.get(f"/admin/workshops/{taller_id}", headers=con_token(token_admin))

    vieja = _visitas(sesion, taller_id)[0]
    vieja.created_at = ahora() - timedelta(days=1)
    sesion.commit()

    cliente.get(f"/admin/workshops/{taller_id}", headers=con_token(token_admin))

    assert len(_visitas(sesion, taller_id)) == 2


def test_dos_admins_distintos_quedan_los_dos(cliente, token_admin, sesion):
    """La ventana es por persona: que Vicente haya entrado no tapa que entro Martin."""
    taller_id, _, _ = _taller_con_una_orden(cliente, token_admin)
    cliente.post(
        "/admin/accounts",
        json={"name": "Martin", "email": "martin@solve.cl", "password": "otra-clave-larga"},
        headers=con_token(token_admin),
    )
    token_martin = entrar(cliente, "martin@solve.cl", clave="otra-clave-larga")

    cliente.get(f"/admin/workshops/{taller_id}", headers=con_token(token_admin))
    cliente.get(f"/admin/workshops/{taller_id}", headers=con_token(token_martin))

    assert len(_visitas(sesion, taller_id)) == 2


def test_mirar_las_ordenes_no_escribe_una_fila_por_click(cliente, token_admin, sesion):
    """Se anota la puerta, no cada paso adentro.

    Para ver cualquier cosa de un taller hay que abrir su ficha primero, asi que con esa
    linea alcanza para saber quien entro. Anotar cada listado y cada orden multiplicaria
    las filas sin agregar una sola respuesta nueva.
    """
    taller_id, _, orden_id = _taller_con_una_orden(cliente, token_admin)

    cliente.get(f"/admin/workshops/{taller_id}/orders", headers=con_token(token_admin))
    cliente.get(
        f"/admin/workshops/{taller_id}/orders/{orden_id}", headers=con_token(token_admin)
    )

    assert _visitas(sesion, taller_id) == []

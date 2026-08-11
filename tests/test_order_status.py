"""Mover la orden de estado: el corazon del producto.

Cambiar el estado hace tres cosas de una: mueve la orden, deja registrado quien la movio
y deja escrito el aviso para el cliente. El mensaje viene redactado por defecto, pero el
mecanico puede reemplazarlo cuando aparece un imprevisto que contar.
"""

from sqlalchemy import select

from app.models import Notification, OrderEvent
from tests.conftest import con_token, crear_cliente_api, crear_vehiculo_api, entrar


def orden_lista(cliente, token, nombre="Juan Perez", telefono="56911111111"):
    cliente_id = crear_cliente_api(cliente, token, nombre=nombre, telefono=telefono)
    vehiculo_id = crear_vehiculo_api(
        cliente, token, cliente_id, patente="ABCD12", marca="Toyota", modelo="Corolla"
    )
    respuesta = cliente.post(
        "/orders",
        json={"clientId": cliente_id, "vehicleId": vehiculo_id, "title": "Revision de frenos"},
        headers=con_token(token),
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["data"]["id"]


def mover(cliente, token, orden_id, estado, mensaje=None):
    cuerpo = {"status": estado}
    if mensaje is not None:
        cuerpo["message"] = mensaje
    return cliente.post(
        f"/orders/{orden_id}/status", json=cuerpo, headers=con_token(token)
    )


def test_mover_el_estado_deja_la_orden_en_el_estado_nuevo(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token)

    respuesta = mover(cliente, token, orden, "listo")

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["order"]["status"] == "listo"


def test_un_estado_inventado_se_rechaza(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token)

    respuesta = mover(cliente, token, orden, "lavandolo")

    assert respuesta.status_code == 422


def test_queda_registrado_quien_movio_la_orden_y_desde_donde(cliente, dueno, sesion):
    """La pregunta del dueno cuando algo sale mal: quien la dio por lista."""
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token)

    mover(cliente, token, orden, "en_reparacion")

    evento = sesion.scalar(select(OrderEvent).where(OrderEvent.order_id == orden))
    assert evento.from_status == "recibido"
    assert evento.to_status == "en_reparacion"
    assert evento.user_id == dueno.id


def test_mover_el_estado_deja_el_aviso_escrito_para_el_cliente(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token, telefono="56911111111")

    respuesta = mover(cliente, token, orden, "listo")

    aviso = respuesta.json()["data"]["notification"]
    assert aviso["toPhone"] == "56911111111"
    assert aviso["status"] == "link_ready"


def test_el_aviso_predeterminado_nombra_al_cliente_y_a_su_auto(cliente, dueno):
    """El cliente tiene que reconocer de que le hablan sin preguntar."""
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token, nombre="Juan Perez")

    respuesta = mover(cliente, token, orden, "listo")

    mensaje = respuesta.json()["data"]["notification"]["message"]
    assert "Juan" in mensaje
    assert "ABCD12" in mensaje


def test_cada_estado_tiene_su_propio_mensaje(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token)

    en_reparacion = mover(cliente, token, orden, "en_reparacion").json()
    listo = mover(cliente, token, orden, "listo").json()

    assert (
        en_reparacion["data"]["notification"]["message"]
        != listo["data"]["notification"]["message"]
    )


def test_el_mecanico_puede_escribir_su_propio_mensaje(cliente, dueno):
    """Para el imprevisto que la plantilla no puede adivinar."""
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token)
    suyo = "Hola Juan, encontramos una fuga en el radiador. Te llamo para explicarte."

    respuesta = mover(cliente, token, orden, "esperando_aprobacion", mensaje=suyo)

    assert respuesta.json()["data"]["notification"]["message"] == suyo


def test_se_guarda_el_mensaje_que_de_verdad_salio(cliente, dueno, sesion):
    """Si manana el cliente reclama, el registro tiene que decir lo que se le escribio."""
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token)
    suyo = "Hola Juan, encontramos una fuga en el radiador."

    mover(cliente, token, orden, "esperando_aprobacion", mensaje=suyo)

    guardado = sesion.scalar(select(Notification).where(Notification.order_id == orden))
    assert guardado.message == suyo
    assert guardado.triggered_by_user_id == dueno.id


def test_dejar_la_orden_en_el_estado_que_ya_tenia_no_avisa_de_nuevo(cliente, dueno, sesion):
    """Dos veces 'listo' es el cliente recibiendo el mismo mensaje dos veces."""
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token)
    mover(cliente, token, orden, "listo")

    respuesta = mover(cliente, token, orden, "listo")

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["notification"] is None
    avisos = sesion.scalars(
        select(Notification).where(Notification.order_id == orden)
    ).all()
    assert len(avisos) == 1


def test_volver_atras_corrige_el_estado_sin_escribirle_al_cliente(cliente, dueno, sesion):
    """El dedazo: el mecanico marca 'entregado' y el auto acaba de entrar.

    Antes, cada toque del estado generaba un aviso: corregirse le mandaba al dueno del
    auto un "gracias por confiar" y despues un "lo recibimos" del mismo trabajo.
    """
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token)
    mover(cliente, token, orden, "entregado")

    respuesta = mover(cliente, token, orden, "recibido")

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["order"]["status"] == "recibido"
    assert respuesta.json()["data"]["notification"] is None
    avisos = sesion.scalars(select(Notification).where(Notification.order_id == orden)).all()
    assert len(avisos) == 1


def test_volver_atras_igual_queda_en_el_historial(cliente, dueno, sesion):
    """Al cliente no se le escribe, pero el dueno del taller tiene que poder verlo."""
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token)
    mover(cliente, token, orden, "listo")
    mover(cliente, token, orden, "en_reparacion")

    eventos = sesion.scalars(select(OrderEvent).where(OrderEvent.order_id == orden)).all()
    assert len(eventos) == 2
    assert eventos[1].from_status == "listo"
    assert eventos[1].to_status == "en_reparacion"


def test_saltarse_estados_hacia_adelante_sigue_avisando(cliente, dueno):
    """El trabajo rapido existe: el auto entra y sale listo el mismo dia."""
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token)

    respuesta = mover(cliente, token, orden, "listo")

    assert respuesta.json()["data"]["notification"] is not None


def test_mover_la_orden_de_otro_taller_responde_no_encontrado(cliente, dueno, dueno_vecino):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    ajena = orden_lista(cliente, token_propio)

    respuesta = mover(cliente, token_vecino, ajena, "listo")

    assert respuesta.status_code == 404


def test_sin_token_no_se_puede_mover_una_orden(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    orden = orden_lista(cliente, token)

    respuesta = cliente.post(f"/orders/{orden}/status", json={"status": "listo"})

    assert respuesta.status_code == 401

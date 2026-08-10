"""Cerrar el ciclo del aviso.

El backend deja el aviso escrito y en `link_ready`. Quien sabe si de verdad se envio es el
frontend, cuando el mecanico aprieta el boton de WhatsApp. Sin este paso, ningun aviso
llega nunca a `sent` y el registro no sirve para responder "esto se le dijo y cuando".
"""

from sqlalchemy import select

from app.models import Notification
from tests.conftest import con_token, crear_cliente_api, crear_vehiculo_api, entrar


def aviso_recien_creado(cliente, token) -> str:
    cliente_id = crear_cliente_api(cliente, token)
    vehiculo_id = crear_vehiculo_api(cliente, token, cliente_id, marca="Toyota", modelo="Corolla")
    orden = cliente.post(
        "/orders",
        json={"clientId": cliente_id, "vehicleId": vehiculo_id, "title": "Frenos"},
        headers=con_token(token),
    ).json()["data"]["id"]
    respuesta = cliente.post(
        f"/orders/{orden}/status", json={"status": "listo"}, headers=con_token(token)
    )
    return respuesta.json()["data"]["notification"]["id"]


def test_marcar_el_aviso_como_enviado_lo_deja_en_sent(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    aviso = aviso_recien_creado(cliente, token)

    respuesta = cliente.post(f"/notifications/{aviso}/sent", headers=con_token(token))

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["status"] == "sent"


def test_queda_la_hora_en_que_se_envio(cliente, dueno, sesion):
    token = entrar(cliente, "dueno@taller.cl")
    aviso = aviso_recien_creado(cliente, token)

    cliente.post(f"/notifications/{aviso}/sent", headers=con_token(token))

    guardado = sesion.scalar(select(Notification).where(Notification.id == aviso))
    assert guardado.sent_at is not None


def test_marcarlo_dos_veces_no_cambia_la_hora_original(cliente, dueno, sesion):
    """El envio ocurrio una vez. La segunda llamada es el frontend reintentando."""
    token = entrar(cliente, "dueno@taller.cl")
    aviso = aviso_recien_creado(cliente, token)
    cliente.post(f"/notifications/{aviso}/sent", headers=con_token(token))
    primera_hora = sesion.scalar(
        select(Notification).where(Notification.id == aviso)
    ).sent_at

    respuesta = cliente.post(f"/notifications/{aviso}/sent", headers=con_token(token))

    assert respuesta.status_code == 200
    sesion.expire_all()
    assert sesion.scalar(
        select(Notification).where(Notification.id == aviso)
    ).sent_at == primera_hora


def test_el_texto_editado_por_el_mecanico_reemplaza_al_borrador(cliente, dueno, sesion):
    """Lo que se guarda es lo que de verdad salio, no el borrador que preparamos.

    El mecanico ve el borrador y a veces lo cambia -aparecio una fuga al desarmar-.
    Si guardamos el borrador, el registro dice una cosa y al cliente le llego otra.
    """
    token = entrar(cliente, "dueno@taller.cl")
    aviso = aviso_recien_creado(cliente, token)

    respuesta = cliente.post(
        f"/notifications/{aviso}/sent",
        json={"message": "Hola Juan, tu auto quedo listo pero apareció una fuga. Te llamo."},
        headers=con_token(token),
    )

    assert respuesta.status_code == 200
    guardado = sesion.scalar(select(Notification).where(Notification.id == aviso))
    assert guardado.message == (
        "Hola Juan, tu auto quedo listo pero apareció una fuga. Te llamo."
    )


def test_sin_texto_el_borrador_queda_tal_cual(cliente, dueno, sesion):
    """El frontend que solo marca enviado, sin mandar nada, tiene que seguir andando."""
    token = entrar(cliente, "dueno@taller.cl")
    aviso = aviso_recien_creado(cliente, token)
    borrador = sesion.scalar(select(Notification).where(Notification.id == aviso)).message

    respuesta = cliente.post(f"/notifications/{aviso}/sent", headers=con_token(token))

    assert respuesta.status_code == 200
    sesion.expire_all()
    assert sesion.scalar(
        select(Notification).where(Notification.id == aviso)
    ).message == borrador


def test_marcarlo_de_nuevo_no_reescribe_el_texto_que_ya_salio(cliente, dueno, sesion):
    """Ya se envio: el texto que leyo el cliente no se puede cambiar despues."""
    token = entrar(cliente, "dueno@taller.cl")
    aviso = aviso_recien_creado(cliente, token)
    cliente.post(
        f"/notifications/{aviso}/sent",
        json={"message": "El texto que salio"},
        headers=con_token(token),
    )

    respuesta = cliente.post(
        f"/notifications/{aviso}/sent",
        json={"message": "Otro texto inventado despues"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 200
    sesion.expire_all()
    assert sesion.scalar(
        select(Notification).where(Notification.id == aviso)
    ).message == "El texto que salio"


def test_un_texto_en_blanco_no_se_acepta(cliente, dueno):
    """Un aviso vacio no es un aviso. Si viene el campo, tiene que traer algo."""
    token = entrar(cliente, "dueno@taller.cl")
    aviso = aviso_recien_creado(cliente, token)

    respuesta = cliente.post(
        f"/notifications/{aviso}/sent", json={"message": "   "}, headers=con_token(token)
    )

    assert respuesta.status_code == 422


def test_un_texto_larguisimo_no_se_acepta(cliente, dueno):
    """El mismo limite que al mover de estado: 1000 caracteres."""
    token = entrar(cliente, "dueno@taller.cl")
    aviso = aviso_recien_creado(cliente, token)

    respuesta = cliente.post(
        f"/notifications/{aviso}/sent",
        json={"message": "a" * 1001},
        headers=con_token(token),
    )

    assert respuesta.status_code == 422


def test_el_aviso_de_otro_taller_no_se_puede_tocar(cliente, dueno, dueno_vecino):
    token_propio = entrar(cliente, "dueno@taller.cl")
    token_vecino = entrar(cliente, "dueno@vecino.cl")
    ajeno = aviso_recien_creado(cliente, token_propio)

    respuesta = cliente.post(f"/notifications/{ajeno}/sent", headers=con_token(token_vecino))

    assert respuesta.status_code == 404


def test_sin_token_no_se_puede_marcar(cliente, dueno):
    token = entrar(cliente, "dueno@taller.cl")
    aviso = aviso_recien_creado(cliente, token)

    respuesta = cliente.post(f"/notifications/{aviso}/sent")

    assert respuesta.status_code == 401

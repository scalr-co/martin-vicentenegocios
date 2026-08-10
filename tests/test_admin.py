"""El panel de administracion de Solve.

No es parte del taller: es el lugar donde Vicente y Martin dan de alta talleres nuevos,
los miran y le devuelven el acceso a un dueno que perdio su clave.

Dos reglas que sostienen todo lo de aca:
- El admin entra con su propia cuenta, no con una clave compartida. Asi se sabe quien hizo que.
- Ser admin de la plataforma NO da acceso a los datos de ningun taller: las ordenes, los
  clientes y los vehiculos siguen filtrando por el taller del token, sin excepciones.
"""

import pytest
from sqlalchemy import select

from app.config import Settings
from app.models import User, Workshop
from tests.conftest import (
    CLAVE_DE_PRUEBA,
    con_token,
    crear_cliente_api,
    crear_vehiculo_api,
    entrar,
)

CLAVE_ADMIN = "clave-de-administracion-de-solve"


@pytest.fixture(autouse=True)
def clave_de_admin_configurada(monkeypatch):
    import app.config

    monkeypatch.setattr(app.config, "settings", Settings(admin_api_key=CLAVE_ADMIN))


def crear_cuenta_admin(cliente, email="vicente@solve.cl", clave=CLAVE_ADMIN):
    cabeceras = {"X-Admin-Key": clave} if clave is not None else {}
    return cliente.post(
        "/admin/accounts",
        json={"name": "Vicente", "email": email, "password": CLAVE_DE_PRUEBA},
        headers=cabeceras,
    )


@pytest.fixture
def token_admin(cliente):
    assert crear_cuenta_admin(cliente).status_code == 201
    return entrar(cliente, "vicente@solve.cl")


def alta_de_taller(cliente, token, **cambios):
    cuerpo = {
        "workshopName": "Taller San Cristobal",
        "workshopPhone": "56987654321",
        "ownerName": "Marcela",
        "email": "marcela@sancristobal.cl",
        "password": "una-clave-larga-de-verdad",
    }
    cuerpo.update(cambios)
    return cliente.post("/admin/workshops", json=cuerpo, headers=con_token(token))


def test_sin_la_clave_no_se_puede_crear_una_cuenta_de_admin(cliente):
    """Es la cuenta mas poderosa del sistema: la puerta es la clave del servidor."""
    respuesta = crear_cuenta_admin(cliente, clave=None)

    assert respuesta.status_code == 403


def test_con_la_clave_queda_creada_y_puede_entrar(cliente):
    respuesta = crear_cuenta_admin(cliente)

    assert respuesta.status_code == 201, respuesta.text
    token = entrar(cliente, "vicente@solve.cl")
    yo = cliente.get("/auth/me", headers=con_token(token))
    assert yo.json()["data"]["user"]["role"] == "platform_admin"


def test_sin_token_no_se_entra_al_panel(cliente):
    assert cliente.get("/admin/workshops").status_code == 401


def test_el_dueno_de_un_taller_no_entra_al_panel(cliente, dueno):
    """Administrar SU taller no es administrar la plataforma."""
    token = entrar(cliente, "dueno@taller.cl")

    assert cliente.get("/admin/workshops", headers=con_token(token)).status_code == 403


def test_el_mecanico_tampoco(cliente, mecanico):
    token = entrar(cliente, "mecanico@taller.cl")

    assert cliente.get("/admin/workshops", headers=con_token(token)).status_code == 403


def test_crear_un_taller_deja_a_su_dueno_listo_para_entrar(cliente, token_admin):
    """La prueba de que el alta sirve no es el 201: es que el dueno pueda entrar."""
    respuesta = alta_de_taller(cliente, token_admin)

    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["data"]["workshop"]["name"] == "Taller San Cristobal"
    entrar(cliente, "marcela@sancristobal.cl", clave="una-clave-larga-de-verdad")


def test_un_correo_repetido_no_crea_un_taller_a_medias(cliente, token_admin):
    alta_de_taller(cliente, token_admin)

    respuesta = alta_de_taller(cliente, token_admin, workshopName="Otro taller")

    assert respuesta.status_code == 409


def test_queda_registrado_quien_dio_de_alta_el_taller(cliente, token_admin, sesion):
    """Es la razon de tener cuentas separadas en vez de una clave compartida."""
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]

    taller = sesion.get(Workshop, taller_id)
    admin = sesion.scalar(select(User).where(User.email == "vicente@solve.cl"))
    assert taller.created_by_user_id == admin.id


def test_la_lista_no_muestra_el_taller_interno_de_solve(cliente, token_admin):
    """Solve no es un taller mecanico: existe solo para colgar las cuentas de admin."""
    alta_de_taller(cliente, token_admin)

    lista = cliente.get("/admin/workshops", headers=con_token(token_admin)).json()["data"]

    nombres = [taller["name"] for taller in lista]
    assert nombres == ["Taller San Cristobal"]


def test_la_lista_dice_cuantas_ordenes_lleva_cada_taller(cliente, token_admin):
    """Sin esto la lista no distingue al taller que lo usa del que se quedo pegado."""
    alta_de_taller(cliente, token_admin)
    token_dueno = entrar(cliente, "marcela@sancristobal.cl", clave="una-clave-larga-de-verdad")
    cliente_id = crear_cliente_api(cliente, token_dueno)
    vehiculo_id = crear_vehiculo_api(cliente, token_dueno, cliente_id)
    cliente.post(
        "/orders",
        json={"clientId": cliente_id, "vehicleId": vehiculo_id, "title": "Frenos"},
        headers=con_token(token_dueno),
    )

    lista = cliente.get("/admin/workshops", headers=con_token(token_admin)).json()["data"]

    assert lista[0]["ordersCount"] == 1
    assert lista[0]["ownerEmail"] == "marcela@sancristobal.cl"


def test_corregir_el_nombre_del_taller_cambia_el_whatsapp(cliente, token_admin):
    """El nombre no es decorativo: sale en el mensaje que lee el cliente del taller."""
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]
    token_dueno = entrar(cliente, "marcela@sancristobal.cl", clave="una-clave-larga-de-verdad")

    respuesta = cliente.patch(
        f"/admin/workshops/{taller_id}",
        json={"name": "Taller San Cristobal Ltda"},
        headers=con_token(token_admin),
    )

    assert respuesta.status_code == 200
    cliente_id = crear_cliente_api(cliente, token_dueno)
    vehiculo_id = crear_vehiculo_api(cliente, token_dueno, cliente_id)
    orden = cliente.post(
        "/orders",
        json={"clientId": cliente_id, "vehicleId": vehiculo_id, "title": "Frenos"},
        headers=con_token(token_dueno),
    ).json()["data"]["id"]
    aviso = cliente.post(
        f"/orders/{orden}/status", json={"status": "listo"}, headers=con_token(token_dueno)
    ).json()["data"]["notification"]

    assert "Taller San Cristobal Ltda" in aviso["message"]


def test_la_clave_nueva_reemplaza_a_la_vieja(cliente, token_admin):
    """Lo que hoy no existe: un dueno que perdio su clave sin perder sus ordenes."""
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]

    respuesta = cliente.post(
        f"/admin/workshops/{taller_id}/owner-password",
        json={"password": "la-clave-nueva-que-le-paso"},
        headers=con_token(token_admin),
    )

    assert respuesta.status_code == 200
    entrar(cliente, "marcela@sancristobal.cl", clave="la-clave-nueva-que-le-paso")
    vieja = cliente.post(
        "/auth/login",
        json={"email": "marcela@sancristobal.cl", "password": "una-clave-larga-de-verdad"},
    )
    assert vieja.status_code == 401


def test_ser_admin_de_la_plataforma_no_da_acceso_a_las_ordenes(cliente, token_admin):
    """La regla que sostiene todo: los datos siguen filtrando por el taller del token."""
    alta_de_taller(cliente, token_admin)
    token_dueno = entrar(cliente, "marcela@sancristobal.cl", clave="una-clave-larga-de-verdad")
    cliente_id = crear_cliente_api(cliente, token_dueno)
    vehiculo_id = crear_vehiculo_api(cliente, token_dueno, cliente_id)
    cliente.post(
        "/orders",
        json={"clientId": cliente_id, "vehicleId": vehiculo_id, "title": "Frenos"},
        headers=con_token(token_dueno),
    )

    ordenes = cliente.get("/orders", headers=con_token(token_admin))

    assert ordenes.status_code == 200
    assert ordenes.json()["data"] == []

"""El panel de administracion de Solve.

No es parte del taller: es el lugar donde Vicente y Martin dan de alta talleres nuevos,
los miran y le devuelven el acceso a un dueno que perdio su clave.

Dos reglas que sostienen todo lo de aca:
- El admin entra con su propia cuenta, no con una clave compartida. Asi se sabe quien hizo que.
- Ser admin de la plataforma NO da acceso a los datos de ningun taller: las ordenes, los
  clientes y los vehiculos siguen filtrando por el taller del token, sin excepciones.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.config import Settings
from app.models import User, Workshop
from scripts.crear_admin import crear_admin
from tests.conftest import (
    con_token,
    crear_cliente_api,
    crear_vehiculo_api,
    entrar,
)

CLAVE_ADMIN = "clave-de-administracion-de-solve"
CLAVE_DEL_ADMIN = "clave-larga-del-admin"


@pytest.fixture(autouse=True)
def clave_de_admin_configurada(monkeypatch):
    import app.config

    monkeypatch.setattr(app.config, "settings", Settings(admin_api_key=CLAVE_ADMIN))


@pytest.fixture
def token_admin(cliente, sesion):
    """La cuenta de admin se crea por consola, que es el unico camino que queda."""
    crear_admin(sesion, "Vicente", "vicente@solve.cl", CLAVE_DEL_ADMIN)
    sesion.commit()
    return entrar(cliente, "vicente@solve.cl", clave=CLAVE_DEL_ADMIN)


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


def test_la_cuenta_de_admin_ya_no_se_puede_crear_por_http(cliente):
    """Creaba la cuenta mas poderosa del sistema con solo una cabecera y sin sesion.

    Con esa llave se le cambiaba la clave al dueno de cualquier taller, se entraba a sus
    datos y no quedaba registro. Ahora la cuenta se crea con scripts/crear_admin.py,
    desde adentro del servidor.
    """
    respuesta = cliente.post(
        "/admin/accounts",
        json={"name": "X", "email": "x@solve.cl", "password": "clave-larga-de-mas"},
        headers={"X-Admin-Key": CLAVE_ADMIN},
    )

    assert respuesta.status_code == 404


def test_la_cuenta_creada_por_consola_puede_entrar(cliente, sesion):
    crear_admin(sesion, "Vicente", "vicente@solve.cl", CLAVE_DEL_ADMIN)
    sesion.commit()

    token = entrar(cliente, "vicente@solve.cl", clave=CLAVE_DEL_ADMIN)

    yo = cliente.get("/auth/me", headers=con_token(token))
    assert yo.json()["data"]["user"]["role"] == "platform_admin"


def test_la_consola_no_deja_crear_dos_cuentas_con_el_mismo_correo(sesion):
    crear_admin(sesion, "Vicente", "vicente@solve.cl", CLAVE_DEL_ADMIN)
    sesion.commit()

    with pytest.raises(HTTPException) as fallo:
        crear_admin(sesion, "Otro", "vicente@solve.cl", CLAVE_DEL_ADMIN)

    assert fallo.value.status_code == 409


def test_la_consola_no_deja_una_clave_corta_en_la_cuenta_mas_poderosa(sesion):
    with pytest.raises(HTTPException) as fallo:
        crear_admin(sesion, "Vicente", "vicente@solve.cl", "corta")

    assert fallo.value.status_code == 422


def test_el_correo_del_admin_tambien_se_normaliza(sesion):
    """La consola y el panel comparten el alta, asi que comparten la normalizacion."""
    admin = crear_admin(sesion, "  Vicente ", "  Vicente@Solve.CL ", CLAVE_DEL_ADMIN)
    sesion.commit()

    assert admin.email == "vicente@solve.cl"
    assert admin.name == "Vicente"


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


def test_el_correo_se_guarda_en_minusculas_y_sin_espacios(cliente, token_admin, sesion):
    """El dueno escribe su correo como le sale. Si una puerta normaliza y otra no, el
    mismo correo entra dos veces y despues el login no sabe a quien se refiere."""
    respuesta = alta_de_taller(cliente, token_admin, email="  Marcela@SanCristobal.CL ")
    assert respuesta.status_code == 201, respuesta.text

    guardado = sesion.scalar(select(User).where(User.role == "owner"))
    assert guardado.email == "marcela@sancristobal.cl"


def test_no_se_puede_repetir_el_correo_aunque_cambie_la_capitalizacion(cliente, token_admin):
    alta_de_taller(cliente, token_admin, email="marcela@sancristobal.cl")

    repetido = alta_de_taller(
        cliente, token_admin, email="MARCELA@sancristobal.cl", workshopName="Otro Taller"
    )

    assert repetido.status_code == 409
    assert repetido.json()["error"]["code"] == "CONFLICT"

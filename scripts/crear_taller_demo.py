"""Crea un taller con datos adentro, para mostrar el producto o para probarlo.

Existe por dos razones. La primera: una cuenta de plataforma **no ve ningun taller** -su
sesion cuelga del taller interno de Solve y `/orders` le devuelve vacio-, asi que con ella
no se puede recorrer el panel del taller ni mostrarselo a nadie. Hacen falta cuentas con
rol `owner` y `mechanic`. La segunda: un panel vacio no demuestra nada, asi que esto deja
clientes, autos y ordenes en distintos estados.

No se manda ni un WhatsApp: los talleres funcionan en modo `link`, o sea que el sistema
deja el texto escrito y alguien tiene que apretar enviar. Los telefonos son inventados.

La clave se teclea a ciegas y no viaja como argumento.

Uso: .venv/Scripts/python.exe scripts/crear_taller_demo.py
"""

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from getpass import getpass

BASE = "https://martin-vicentenegocios-production.up.railway.app"
PANEL = "https://tallertrack-nine.vercel.app"

# Tres autos en tres momentos distintos, para que el tablero cuente una historia.
TRABAJOS = [
    ("Ana Fuentes", "56911111111", "JKLM45", "Toyota", "Yaris", "Mantencion de 40.000", "en_reparacion"),
    ("Carlos Vera", "56922222222", "PQRS78", "Chevrolet", "Sail", "Ruido en el freno delantero", "esperando_aprobacion"),
    ("Marta Lillo", "56933333333", "TUVW90", "Suzuki", "Swift", "Cambio de embrague", "listo"),
]


def pedir(metodo, ruta, cuerpo=None, token=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    peticion = urllib.request.Request(BASE + ruta, data=datos, method=metodo)
    peticion.add_header("Content-Type", "application/json")
    if token:
        peticion.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(peticion, timeout=20) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def exigir(estado, respuesta, que: str):
    if estado >= 400:
        print(f"\n[x] {que} fallo ({estado}): {respuesta}")
        sys.exit(1)
    return respuesta


def main() -> int:
    print("Crea un taller de demostracion EN PRODUCCION, con datos adentro.\n")

    correo_admin = input("Tu correo de admin: ").strip()
    clave_admin = getpass("Tu clave (no se ve): ")

    nombre = input("\nNombre del taller demo [Taller San Cristobal]: ").strip() or "Taller San Cristobal"
    plan = input("Plan (basico/plus) [basico]: ").strip() or "basico"
    clave_demo = getpass("Clave para las cuentas demo (minimo 8, la vas a usar tu): ")
    if len(clave_demo) < 8:
        print("\n[x] La clave necesita al menos 8 caracteres.")
        return 1

    estado, sesion = pedir("POST", "/auth/login", {"email": correo_admin, "password": clave_admin})
    exigir(estado, sesion, "El login")
    token_admin = sesion["data"]["token"]
    if sesion["data"]["user"]["role"] != "platform_admin":
        print("\n[x] Esa cuenta no es de plataforma: no puede dar de alta talleres.")
        return 1

    sello = datetime.now().strftime("%m%d%H%M")
    correo_dueno = f"dueno.demo{sello}@motorping.cl"
    correo_mecanico = f"mecanico.demo{sello}@motorping.cl"

    estado, alta = pedir("POST", "/admin/workshops", {
        "workshopName": nombre,
        "workshopPhone": "56912345678",
        "ownerName": "Roberto Munoz",
        "email": correo_dueno,
        "password": clave_demo,
        "plan": plan,
    }, token=token_admin)
    exigir(estado, alta, "El alta del taller")
    print(f"\n  [ok] Taller creado: {alta['data']['workshop']['name']} (plan {alta['data']['workshop']['plan']})")

    estado, sesion_dueno = pedir("POST", "/auth/login", {"email": correo_dueno, "password": clave_demo})
    exigir(estado, sesion_dueno, "El login del dueno")
    token_dueno = sesion_dueno["data"]["token"]

    estado, _ = pedir("POST", "/users", {
        "name": "Pedro Soto", "email": correo_mecanico, "password": clave_demo,
    }, token=token_dueno)
    exigir(estado, _, "El alta del mecanico")
    print("  [ok] Mecanico creado")

    for nombre_cliente, telefono, patente, marca, modelo, titulo, estado_final in TRABAJOS:
        _, cliente = pedir("POST", "/clients", {"name": nombre_cliente, "phone": telefono}, token=token_dueno)
        _, vehiculo = pedir("POST", "/vehicles", {
            "clientId": cliente["data"]["id"], "plate": patente, "brand": marca, "model": modelo,
        }, token=token_dueno)
        _, orden = pedir("POST", "/orders", {
            "clientId": cliente["data"]["id"], "vehicleId": vehiculo["data"]["id"], "title": titulo,
        }, token=token_dueno)
        pedir("POST", f"/orders/{orden['data']['id']}/status", {"status": estado_final}, token=token_dueno)
        print(f"  [ok] {patente} {marca} {modelo} - {titulo} ({estado_final})")

    print("\n" + "=" * 70)
    print("LISTO. Entra en:", PANEL)
    print("=" * 70)
    print(f"  Como DUENO:    {correo_dueno}")
    print(f"  Como MECANICO: {correo_mecanico}")
    print("  Con la clave que acabas de escribir.")
    print()
    print("  El dueno ve todo y ademas administra a su equipo.")
    print("  El mecanico ve las ordenes y avisa por WhatsApp, pero /users le da 403.")
    print()
    print("  Cuando termines, suspende o da de baja el taller desde el panel de admin")
    print("  para que no ensucie la lista de talleres de verdad.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

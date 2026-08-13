"""Comprueba contra produccion que el deploy llego de verdad.

Existe por una leccion cara: el 11-08 el push quedo sin correr y produccion siguio 24 h
con la version vieja mientras todos creiamos que estaba desplegada. Un "te dejo el
comando" no es un deploy: hay que mirar el servidor.

La clave se teclea a ciegas y no viaja como argumento, asi que no queda en el historial
del shell ni en `ps`. Lo unico que se imprime son estados y conteos.

Uso: .venv/Scripts/python.exe scripts/verificar_produccion.py
"""

import json
import ssl
import sys
import urllib.error
import urllib.request
from getpass import getpass

BASE = "https://martin-vicentenegocios-production.up.railway.app"

CAMPOS_DEL_TALLER = ("plan", "status", "suspendedUntil", "suspendIndefinite")
TOPE_BASICO = 3


def pedir(ruta: str, metodo: str = "GET", cuerpo=None, token: str | None = None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    peticion = urllib.request.Request(BASE + ruta, data=datos, method=metodo)
    peticion.add_header("Content-Type", "application/json")
    if token:
        peticion.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(peticion, timeout=20, context=ssl.create_default_context()) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def main() -> int:
    print(f"Servidor: {BASE}\n")

    estado, salud = pedir("/health")
    print(f"1. /health -> {estado} {salud}")
    print(f"2. /docs   -> {pedir('/docs')[0]} (tiene que ser 404 en produccion)")

    correo = input("\nCorreo de tu cuenta: ").strip()
    clave = getpass("Clave (no se ve, no queda en el historial): ")

    estado, respuesta = pedir("/auth/login", "POST", {"email": correo, "password": clave})
    if estado != 200:
        print(f"\n[x] El login respondio {estado}: {respuesta}")
        return 1

    token = respuesta["data"]["token"]
    taller = respuesta["data"]["workshop"]
    rol = respuesta["data"]["user"]["role"]

    faltantes = [campo for campo in CAMPOS_DEL_TALLER if campo not in taller]
    if faltantes:
        print(f"\n[x] LA VERSION VIEJA SIGUE ARRIBA: al taller del login le faltan {faltantes}")
        return 1
    print(f"\n3. El login trae los campos nuevos: plan={taller['plan']} status={taller['status']}")

    if rol != "platform_admin":
        print(f"\n(Tu cuenta es '{rol}', asi que hasta aca llega la revision.)")
        return 0

    estado, lista = pedir("/admin/workshops", token=token)
    if estado != 200:
        print(f"\n[x] GET /admin/workshops respondio {estado}: {lista}")
        return 1

    talleres = lista["data"]
    print(f"\n4. {len(talleres)} taller(es) en produccion:\n")
    apretados = []
    for taller in talleres:
        _, equipo = pedir(f"/admin/workshops/{taller['id']}/users", token=token)
        mecanicos = [
            persona
            for persona in equipo.get("data", [])
            if persona["role"] == "mechanic" and persona["active"]
        ]
        aviso = ""
        if taller["plan"] == "basico" and len(mecanicos) >= TOPE_BASICO:
            aviso = "  <-- en el tope: no puede sumar otro sin pasar a plus"
            apretados.append(taller["name"])
        print(
            f"   {taller['name'][:34]:<34} plan={taller['plan']:<7} "
            f"status={taller['status']:<9} mecanicos activos={len(mecanicos)} "
            f"ordenes={taller['ordersCount']}{aviso}"
        )

    print()
    if apretados:
        print(f"[!] Revisar: {', '.join(apretados)} llego al tope del plan basico.")
    else:
        print("[ok] Ningun taller queda apretado por el tope de mecanicos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

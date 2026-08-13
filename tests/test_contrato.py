"""El contrato de salida: lo que la API promete devolver.

Con `/docs` cerrada en produccion, `openapi.json` **es** el contrato: es el archivo que
mira quien escribe el frontend para saber como se llaman los campos. Durante un tiempo
decia lo que entra y nada de lo que sale -ninguna ruta declaraba `response_model`-, asi
que los nombres se adivinaban, y adivinar salio caro: el frontend leia
`latestNotification` de un endpoint que nunca lo devolvio, y ningun aviso llegaba a
marcarse como enviado.

Estos dos tests existen para que no vuelva a pasar. Fallan cuando alguien agrega una ruta
sin declarar que devuelve, o cambia el contrato y no regenera el archivo.
"""

import json
from pathlib import Path

from fastapi.routing import APIRoute

from app.main import crear_app

RAIZ = Path(__file__).resolve().parent.parent

SIN_CUERPO = 204


def test_toda_ruta_declara_lo_que_devuelve():
    """Salvo las que no devuelven nada: un 204 no tiene cuerpo que describir."""
    aplicacion = crear_app()

    calladas = [
        f"{sorted(ruta.methods)[0]} {ruta.path}"
        for ruta in aplicacion.routes
        if isinstance(ruta, APIRoute)
        and ruta.response_model is None
        and ruta.status_code != SIN_CUERPO
    ]

    assert calladas == []


def test_el_openapi_del_repo_esta_al_dia():
    """El archivo versionado tiene que ser el que la aplicacion genera hoy.

    Ya estuvo congelado en 4 rutas cuando la API tenia 14, y nadie se entero hasta que un
    frontend se escribio contra el. Se regenera con:
    `.venv/Scripts/python.exe scripts/exportar_openapi.py`
    """
    guardado = json.loads((RAIZ / "openapi.json").read_text(encoding="utf-8"))

    assert guardado == crear_app().openapi()

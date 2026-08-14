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

from app.main import crear_app

RAIZ = Path(__file__).resolve().parent.parent

SIN_CUERPO = "204"


def rutas_calladas(esquema: dict) -> list[str]:
    """Las respuestas exitosas que no dicen que devuelven.

    Se pregunta sobre el esquema y no sobre `app.routes` a proposito. La primera version
    de este guardian recorria las rutas del objeto y **no comprobaba nada**: desde FastAPI
    0.141 `include_router` ya no copia las rutas a la aplicacion, las envuelve en un
    `_IncludedRouter`, asi que el recorrido solo veia `/health` y pasaba siempre. El
    esquema, en cambio, es exactamente lo que lee quien escribe el frontend.
    """
    return [
        f"{metodo.upper()} {ruta} -> {codigo}"
        for ruta, operaciones in esquema["paths"].items()
        for metodo, operacion in operaciones.items()
        for codigo, respuesta in operacion.get("responses", {}).items()
        if codigo.startswith("2") and codigo != SIN_CUERPO and "content" not in respuesta
    ]


def test_toda_ruta_declara_lo_que_devuelve():
    """Salvo las que no devuelven nada: un 204 no tiene cuerpo que describir."""
    assert rutas_calladas(crear_app().openapi()) == []


def test_el_guardian_sabe_fallar():
    """Un guardian que no puede fallar es peor que no tener guardian: da confianza sin
    darla. Fue exactamente lo que paso con la version anterior de este archivo."""
    esquema_con_una_muda = {
        "paths": {
            "/muda": {"get": {"responses": {"200": {"description": "no dice que devuelve"}}}},
            "/sin-cuerpo": {"delete": {"responses": {"204": {"description": "vacio"}}}},
            "/buena": {
                "get": {"responses": {"200": {"content": {"application/json": {}}}}}
            },
        }
    }

    assert rutas_calladas(esquema_con_una_muda) == ["GET /muda -> 200"]


def test_el_openapi_del_repo_esta_al_dia():
    """El archivo versionado tiene que ser el que la aplicacion genera hoy.

    Ya estuvo congelado en 4 rutas cuando la API tenia 14, y nadie se entero hasta que un
    frontend se escribio contra el. Se regenera con:
    `.venv/Scripts/python.exe scripts/exportar_openapi.py`
    """
    guardado = json.loads((RAIZ / "openapi.json").read_text(encoding="utf-8"))

    assert guardado == crear_app().openapi()

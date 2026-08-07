"""Escribe openapi.json a la raiz del repositorio.

Se versiona a proposito: asi Martin ve en cada commit que cambio del contrato
sin tener que levantar la API.

Uso: .venv/Scripts/python.exe scripts/exportar_openapi.py
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app.main import app  # noqa: E402  (debe ir despues de ajustar sys.path)

destino = RAIZ / "openapi.json"
destino.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False), encoding="utf-8")
print(f"openapi.json escrito: {destino}")

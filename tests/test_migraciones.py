"""Que un repo recien clonado levante.

El resto de la suite crea las tablas desde los modelos (`Base.metadata.create_all`), asi
que la suite en verde no dice nada sobre si las migraciones corren. Este archivo es el
unico que lo comprueba, y por eso existe: una migracion que aplica la mitad y no se puede
reintentar es la que un dia deja la base de produccion a medias.

La direccion de la base se pisa en `app.config.settings` porque es de ahi de donde la
lee `alembic/env.py`, no de `alembic.ini`.
"""

import app.config
from alembic import command
from alembic.config import Config


def _apuntando_a(monkeypatch, ruta) -> Config:
    monkeypatch.setattr(app.config.settings, "database_url", f"sqlite:///{ruta}")
    return Config("alembic.ini")


def test_las_migraciones_llegan_hasta_el_final(tmp_path, monkeypatch):
    """Lo que hace quien clona el repo y sigue el README."""
    command.upgrade(_apuntando_a(monkeypatch, tmp_path / "prueba.db"), "head")


def test_las_migraciones_se_pueden_deshacer_y_volver_a_aplicar(tmp_path, monkeypatch):
    """Antes fallaba a la mitad y el segundo intento moria con 'duplicate column'.

    SQLite no deshace DDL: la columna quedaba agregada aunque la migracion no terminara,
    y no habia forma de salir sin borrar el archivo de la base a mano.
    """
    config = _apuntando_a(monkeypatch, tmp_path / "prueba.db")

    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")

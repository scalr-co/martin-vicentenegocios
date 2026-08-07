"""La clave por defecto esta escrita en el repositorio, que es publico.

Si la aplicacion arrancara en produccion con ella, cualquiera que lea el codigo
podria fabricarse un token valido y entrar como dueno de cualquier taller.
Preferimos que no parta antes que partir insegura.
"""

import pytest

from app.config import ConfiguracionInvalida, Settings

CLAVE_PROPIA = "una-clave-larga-generada-al-azar-para-produccion"


def test_en_produccion_la_clave_por_defecto_impide_arrancar():
    with pytest.raises(ConfiguracionInvalida):
        Settings(entorno="produccion")


def test_en_produccion_una_clave_propia_esta_bien():
    config = Settings(entorno="produccion", jwt_secret=CLAVE_PROPIA)

    assert config.jwt_secret == CLAVE_PROPIA


def test_en_desarrollo_la_clave_por_defecto_esta_permitida():
    config = Settings(entorno="desarrollo")

    assert config.jwt_secret


def test_en_produccion_una_clave_corta_tampoco_sirve():
    with pytest.raises(ConfiguracionInvalida):
        Settings(entorno="produccion", jwt_secret="corta")

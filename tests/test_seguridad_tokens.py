from datetime import timedelta

import jwt
import pytest

from app.security.tokens import DatosToken, TokenInvalido, crear_token, leer_token


def test_lo_que_se_guarda_en_el_token_se_lee_de_vuelta():
    token = crear_token(user_id="u-1", workshop_id="w-1", role="owner", token_version=1)

    datos = leer_token(token)

    assert datos == DatosToken(
        user_id="u-1", workshop_id="w-1", role="owner", token_version=1
    )


def test_un_token_alterado_se_rechaza():
    token = crear_token(user_id="u-1", workshop_id="w-1", role="owner", token_version=1)

    with pytest.raises(TokenInvalido):
        leer_token(token[:-2] + "xy")


def test_un_token_firmado_con_otra_clave_se_rechaza():
    """Sin esto cualquiera podria fabricarse un token y entrar como dueno de otro taller."""
    ajeno = jwt.encode(
        {"sub": "u-9", "workshop_id": "w-9", "role": "owner"},
        "la-clave-de-otro-servidor-cualquiera-distinta-de-la-nuestra",
        algorithm="HS256",
    )

    with pytest.raises(TokenInvalido):
        leer_token(ajeno)


def test_un_token_vencido_se_rechaza():
    token = crear_token(
        user_id="u-1",
        workshop_id="w-1",
        role="owner",
        token_version=1,
        duracion=timedelta(seconds=-1),
    )

    with pytest.raises(TokenInvalido):
        leer_token(token)


def test_un_texto_cualquiera_no_pasa_por_token():
    with pytest.raises(TokenInvalido):
        leer_token("esto-no-es-un-token")

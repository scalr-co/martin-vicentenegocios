"""El equipo del taller: quien trabaja aca y quien ya no.

Lo administra el dueno, no Solve. El taller no puede quedar esperando a que le contesten
para dar de alta al mecanico que empieza el lunes.

La regla que sostiene todo lo de aca: un dueno solo alcanza a la gente de SU taller. Al
tocar a alguien de otro recibe 404 y no 403, porque un 403 confirmaria que ese id existe.
"""

from tests.conftest import con_token, entrar

CLAVE_NUEVA = "clave-nueva-del-mecanico"


def nuevo_mecanico(cliente, token, **cambios):
    cuerpo = {
        "name": "Pedro Soto",
        "email": "pedro@taller.cl",
        "password": "una-clave-de-verdad",
    }
    cuerpo.update(cambios)
    return cliente.post("/users", json=cuerpo, headers=con_token(token))


def test_el_dueno_crea_un_mecanico_y_el_mecanico_entra(cliente, sesion, dueno):
    token = entrar(cliente, dueno.email)

    creado = nuevo_mecanico(cliente, token)

    assert creado.status_code == 201, creado.text
    datos = creado.json()["data"]
    assert datos["role"] == "mechanic"
    assert datos["active"] is True
    assert "passwordHash" not in datos
    assert entrar(cliente, "pedro@taller.cl", clave="una-clave-de-verdad")


def test_el_dueno_no_puede_fabricarse_otro_dueno(cliente, sesion, dueno):
    """El rol lo pone el sistema. Si el cuerpo pudiera elegirlo, cualquier dueno se
    clonaria a si mismo y la guarda del ultimo dueno activo dejaria de servir."""
    token = entrar(cliente, dueno.email)

    creado = nuevo_mecanico(cliente, token, role="owner")

    assert creado.status_code == 201
    assert creado.json()["data"]["role"] == "mechanic"


def test_no_se_repite_un_correo_de_otro_taller(cliente, sesion, dueno, dueno_vecino):
    """El correo es unico en todo el sistema: es con lo que se entra, sin elegir taller."""
    token = entrar(cliente, dueno.email)

    creado = nuevo_mecanico(cliente, token, email=dueno_vecino.email)

    assert creado.status_code == 409
    assert creado.json()["error"]["code"] == "CONFLICT"


def test_el_dueno_ve_a_su_equipo_entero(cliente, sesion, dueno, mecanico):
    token = entrar(cliente, dueno.email)

    lista = cliente.get("/users", headers=con_token(token))

    assert lista.status_code == 200
    correos = {u["email"] for u in lista.json()["data"]}
    assert correos == {dueno.email, mecanico.email}


def test_el_dueno_no_ve_a_la_gente_del_taller_vecino(cliente, sesion, dueno, dueno_vecino):
    token = entrar(cliente, dueno.email)

    lista = cliente.get("/users", headers=con_token(token)).json()["data"]

    assert dueno_vecino.email not in {u["email"] for u in lista}


def test_el_mecanico_no_administra_el_equipo(cliente, sesion, dueno, mecanico):
    """Administrar el taller es del dueno. El mecanico opera las ordenes."""
    token = entrar(cliente, mecanico.email)

    assert cliente.get("/users", headers=con_token(token)).status_code == 403
    assert nuevo_mecanico(cliente, token, email="otro@taller.cl").status_code == 403


def test_sin_sesion_no_se_entra(cliente, sesion, dueno):
    assert cliente.get("/users").status_code == 401

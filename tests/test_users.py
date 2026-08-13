"""El equipo del taller: quien trabaja aca y quien ya no.

Lo administra el dueno, no Solve. El taller no puede quedar esperando a que le contesten
para dar de alta al mecanico que empieza el lunes.

La regla que sostiene todo lo de aca: un dueno solo alcanza a la gente de SU taller. Al
tocar a alguien de otro recibe 404 y no 403, porque un 403 confirmaria que ese id existe.
"""

from tests.conftest import CLAVE_DE_PRUEBA, con_token, entrar

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


def test_desactivar_a_un_mecanico_lo_deja_fuera_al_instante(cliente, sesion, dueno, mecanico):
    token_dueno = entrar(cliente, dueno.email)
    token_mecanico = entrar(cliente, mecanico.email)
    assert cliente.get("/clients", headers=con_token(token_mecanico)).status_code == 200

    apagado = cliente.patch(
        f"/users/{mecanico.id}", json={"active": False}, headers=con_token(token_dueno)
    )

    assert apagado.status_code == 200
    assert apagado.json()["data"]["active"] is False
    # No hay que esperar a que venza su token: se cae en el siguiente request.
    assert cliente.get("/clients", headers=con_token(token_mecanico)).status_code == 401


def test_reactivar_a_un_mecanico_le_devuelve_el_acceso(cliente, sesion, dueno, mecanico):
    token = entrar(cliente, dueno.email)
    cliente.patch(f"/users/{mecanico.id}", json={"active": False}, headers=con_token(token))

    encendido = cliente.patch(
        f"/users/{mecanico.id}", json={"active": True}, headers=con_token(token)
    )

    assert encendido.status_code == 200
    assert entrar(cliente, mecanico.email)


def test_el_desactivado_sigue_saliendo_en_la_lista(cliente, sesion, dueno, mecanico):
    token = entrar(cliente, dueno.email)
    cliente.patch(f"/users/{mecanico.id}", json={"active": False}, headers=con_token(token))

    lista = cliente.get("/users", headers=con_token(token)).json()["data"]

    apagados = [u for u in lista if u["email"] == mecanico.email]
    assert apagados and apagados[0]["active"] is False


def test_nadie_se_desactiva_a_si_mismo(cliente, sesion, dueno):
    """Es el candado que deja a la persona fuera de su propia casa."""
    token = entrar(cliente, dueno.email)

    respuesta = cliente.patch(
        f"/users/{dueno.id}", json={"active": False}, headers=con_token(token)
    )

    assert respuesta.status_code == 409
    assert cliente.get("/users", headers=con_token(token)).status_code == 200


def test_el_taller_nunca_se_queda_sin_dueno_activo(cliente, sesion, dueno):
    """La invariante que sostiene todo: siempre queda un dueno que pueda administrar.

    No hace falta una guarda aparte que cuente los duenos. Quien hace la peticion ES un
    dueno activo -`solo_dueno` lo exige y `usuario_actual` verifica que este activo-, asi
    que apagando a OTRO nunca puede llegar a cero, y apagarse a si mismo esta prohibido.
    Entre esas dos cosas el conjunto no se puede vaciar.
    """
    from tests.conftest import crear_usuario

    socio = crear_usuario(sesion, dueno.workshop, email="socio@taller.cl", role="owner")
    token = entrar(cliente, dueno.email)

    apagado = cliente.patch(
        f"/users/{socio.id}", json={"active": False}, headers=con_token(token)
    )
    assert apagado.status_code == 200

    # Queda uno: el que lo apago. Y ese no se puede apagar a si mismo.
    assert cliente.patch(
        f"/users/{dueno.id}", json={"active": False}, headers=con_token(token)
    ).status_code == 409

    equipo = cliente.get("/users", headers=con_token(token)).json()["data"]
    duenos_activos = [u for u in equipo if u["role"] == "owner" and u["active"]]
    assert len(duenos_activos) == 1


def test_el_dueno_no_toca_a_nadie_del_taller_vecino(cliente, sesion, dueno, dueno_vecino):
    token = entrar(cliente, dueno.email)

    respuesta = cliente.patch(
        f"/users/{dueno_vecino.id}", json={"active": False}, headers=con_token(token)
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "NOT_FOUND"


def test_resetear_la_clave_de_un_mecanico(cliente, sesion, dueno, mecanico):
    token = entrar(cliente, dueno.email)

    cambio = cliente.post(
        f"/users/{mecanico.id}/password",
        json={"password": CLAVE_NUEVA},
        headers=con_token(token),
    )

    assert cambio.status_code == 200
    assert entrar(cliente, mecanico.email, clave=CLAVE_NUEVA)
    vieja = cliente.post(
        "/auth/login", json={"email": mecanico.email, "password": CLAVE_DE_PRUEBA}
    )
    assert vieja.status_code == 401


def test_cambiar_la_clave_corta_la_sesion_que_estaba_abierta(cliente, sesion, dueno, mecanico):
    """Si no, quien tuviera el token de antes sigue adentro hasta 12 horas mas, con una
    clave que ya no sirve. Es lo mismo que hace el panel con la clave del dueno."""
    token_dueno = entrar(cliente, dueno.email)
    token_viejo = entrar(cliente, mecanico.email)
    assert cliente.get("/clients", headers=con_token(token_viejo)).status_code == 200

    cliente.post(
        f"/users/{mecanico.id}/password",
        json={"password": CLAVE_NUEVA},
        headers=con_token(token_dueno),
    )

    assert cliente.get("/clients", headers=con_token(token_viejo)).status_code == 401


def test_no_se_resetea_la_clave_de_otro_taller(cliente, sesion, dueno, dueno_vecino):
    token = entrar(cliente, dueno.email)

    respuesta = cliente.post(
        f"/users/{dueno_vecino.id}/password",
        json={"password": CLAVE_NUEVA},
        headers=con_token(token),
    )

    assert respuesta.status_code == 404
    # Y su clave de siempre le sigue sirviendo.
    assert entrar(cliente, dueno_vecino.email)


def test_la_clave_corta_no_se_acepta(cliente, sesion, dueno, mecanico):
    token = entrar(cliente, dueno.email)

    respuesta = cliente.post(
        f"/users/{mecanico.id}/password",
        json={"password": "corta"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 422

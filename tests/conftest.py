"""Andamiaje comun de los tests.

Cada test recibe una base de datos SQLite en memoria, recien creada y vacia. Es rapida
y no necesita que haya un Postgres corriendo. Produccion usa Postgres; las tablas de
TallerTrack no usan nada especifico de un motor, asi que la diferencia no nos afecta.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, obtener_sesion
from app.main import app
from app.models import User, Workshop
from app.security.passwords import hashear

CLAVE_DE_PRUEBA = "clave-de-prueba"


@pytest.fixture
def sesion():
    motor = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(motor)
    fabrica = sessionmaker(bind=motor, expire_on_commit=False)
    with fabrica() as abierta:
        yield abierta
    motor.dispose()


@pytest.fixture
def cliente(sesion):
    app.dependency_overrides[obtener_sesion] = lambda: sesion
    with TestClient(app) as abierto:
        yield abierto
    app.dependency_overrides.clear()


def crear_taller(sesion: Session, nombre: str = "Taller Los Alerces") -> Workshop:
    taller = Workshop(name=nombre, phone="56912345678")
    sesion.add(taller)
    sesion.commit()
    return taller


def crear_usuario(
    sesion: Session,
    taller: Workshop,
    email: str,
    role: str = "owner",
    nombre: str = "Vicente",
) -> User:
    usuario = User(
        workshop_id=taller.id,
        name=nombre,
        email=email,
        password_hash=hashear(CLAVE_DE_PRUEBA),
        role=role,
    )
    sesion.add(usuario)
    sesion.commit()
    return usuario


def con_token(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def crear_cliente_api(cliente, token, nombre="Juan Perez", telefono="56911111111") -> str:
    """Crea el cliente por la API, como lo haria el mecanico, y devuelve su id."""
    respuesta = cliente.post(
        "/clients",
        json={"name": nombre, "phone": telefono},
        headers=con_token(token),
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["data"]["id"]


def crear_vehiculo_api(
    cliente, token, cliente_id, patente="ABCD12", marca=None, modelo=None
) -> str:
    cuerpo = {"clientId": cliente_id, "plate": patente}
    if marca is not None:
        cuerpo["brand"] = marca
    if modelo is not None:
        cuerpo["model"] = modelo
    respuesta = cliente.post("/vehicles", json=cuerpo, headers=con_token(token))
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["data"]["id"]


def entrar(cliente, email: str, clave: str = CLAVE_DE_PRUEBA) -> str:
    """Hace login de verdad y devuelve el token. Nada de fabricar tokens a mano."""
    respuesta = cliente.post("/auth/login", json={"email": email, "password": clave})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["data"]["token"]


@pytest.fixture
def taller(sesion):
    return crear_taller(sesion)


@pytest.fixture
def dueno(sesion, taller):
    return crear_usuario(sesion, taller, email="dueno@taller.cl", role="owner")


@pytest.fixture
def mecanico(sesion, taller):
    return crear_usuario(sesion, taller, email="mecanico@taller.cl", role="mechanic", nombre="Pedro")


@pytest.fixture
def taller_vecino(sesion):
    """Un segundo taller, para comprobar que ninguno ve los datos del otro."""
    return crear_taller(sesion, nombre="Taller El Vecino")


@pytest.fixture
def dueno_vecino(sesion, taller_vecino):
    return crear_usuario(sesion, taller_vecino, email="dueno@vecino.cl", role="owner", nombre="Ana")

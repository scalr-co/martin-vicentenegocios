from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.errores import registrar_manejadores
from app.schemas.base import Respuesta, Salud
from app.routes import (
    admin,
    admin_soporte,
    auth,
    clients,
    notifications,
    orders,
    statuses,
    users,
    vehicles,
)


def crear_app() -> FastAPI:
    """Arma la aplicacion leyendo la configuracion en el momento, no al importar.

    Asi los tests pueden levantarla como si fuera produccion sin tocar el .env de la
    maquina, que es la unica forma de comprobar lo que se apaga alla.
    """
    ajustes = config.settings

    # En produccion la documentacion no se publica. Con ella abierta, cualquiera lista
    # las rutas -incluidas las de /admin- y ve el nombre de la cabecera de
    # administracion. Para trabajar sirve; para estar en internet, no.
    sin_documentacion = ajustes.es_produccion

    aplicacion = FastAPI(
        title="Motor Ping API",
        docs_url=None if sin_documentacion else "/docs",
        redoc_url=None if sin_documentacion else "/redoc",
        openapi_url=None if sin_documentacion else "/openapi.json",
    )

    registrar_manejadores(aplicacion)

    aplicacion.add_middleware(
        CORSMiddleware,
        allow_origins=ajustes.origenes_permitidos,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    aplicacion.include_router(auth.router)
    aplicacion.include_router(clients.router)
    aplicacion.include_router(vehicles.router)
    aplicacion.include_router(orders.router)
    aplicacion.include_router(notifications.router)
    aplicacion.include_router(statuses.router)
    aplicacion.include_router(users.router)
    aplicacion.include_router(admin.router)
    aplicacion.include_router(admin_soporte.router)

    @aplicacion.get("/health", response_model=Respuesta[Salud])
    def health():
        return {"data": {"status": "ok"}}

    return aplicacion


app = crear_app()

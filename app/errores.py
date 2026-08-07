"""Un solo formato de error para toda la API.

FastAPI responde por defecto { "detail": ... }. El contrato acordado con el frontend es
{ "error": { "message", "code" } }. Estos manejadores traducen todo a esa forma, para que
Martin no tenga que programar dos caminos distintos.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as ExcepcionHTTP

CODIGOS_POR_ESTADO = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_ERROR",
}


def respuesta_de_error(estado: int, mensaje: str, codigo: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=estado,
        content={
            "error": {
                "message": mensaje,
                "code": codigo or CODIGOS_POR_ESTADO.get(estado, "ERROR"),
            }
        },
    )


def _mensaje_de_validacion(error: RequestValidationError) -> str:
    """Convierte el primer problema en algo legible: 'email: no es un correo valido'."""
    fallas = error.errors()
    if not fallas:
        return "Los datos enviados no son validos"

    primera = fallas[0]
    partes = [str(p) for p in primera.get("loc", ()) if p not in ("body", "query", "path")]
    campo = ".".join(partes)
    detalle = primera.get("msg", "valor invalido")
    return f"{campo}: {detalle}" if campo else detalle


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ExcepcionHTTP)
    async def _errores_http(_: Request, error: ExcepcionHTTP) -> JSONResponse:
        return respuesta_de_error(error.status_code, str(error.detail))

    @app.exception_handler(RequestValidationError)
    async def _errores_de_validacion(_: Request, error: RequestValidationError) -> JSONResponse:
        return respuesta_de_error(422, _mensaje_de_validacion(error), "VALIDATION_ERROR")

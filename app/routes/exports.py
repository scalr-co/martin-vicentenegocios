"""Llevarse los datos del taller en un archivo. La otra ventaja del plan Plus.

Un taller que puede exportar sus clientes no esta atrapado, y eso es parte de lo que se
vende: los datos son suyos. Por eso el archivo sale completo y sin paginar.

Quien lo abre es el dueno de un taller en Chile, con Excel. De ahi las dos decisiones que
parecen detalles y no lo son: separador `;` -en la configuracion regional chilena la coma
es el separador decimal, asi que con comas Excel mete todo en una sola columna- y BOM al
principio, o los acentos y las enes salen rotos.
"""

import csv
import io

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import Client, Order, User
from app.security.dependencias import solo_plan_plus
from app.services.presentacion import ETIQUETAS_DE_ESTADO

router = APIRouter(prefix="/exports", tags=["exports"])

SEPARADOR = ";"
BOM = "﻿"

# Lo que sale de aca no es JSON, asi que el contrato lo declara a mano: sin esto,
# openapi.json diria que estas dos rutas no devuelven nada.
ARCHIVO_CSV = {
    200: {
        "description": "El archivo, listo para abrir en Excel",
        "content": {"text/csv": {"schema": {"type": "string", "format": "binary"}}},
    }
}


def _archivo(nombre: str, encabezados: list[str], filas: list[list[str]]) -> Response:
    """Arma el CSV y lo manda como algo que se guarda, no como algo que se mira."""
    papel = io.StringIO()
    escritor = csv.writer(papel, delimiter=SEPARADOR, lineterminator="\r\n")
    escritor.writerow(encabezados)
    escritor.writerows(filas)

    return Response(
        content=BOM + papel.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


def _fecha(valor) -> str:
    """Como la lee una persona, no como la guarda la base."""
    return valor.strftime("%d-%m-%Y") if valor else ""


@router.get("/clients", response_class=Response, responses=ARCHIVO_CSV)
def clientes(
    usuario: User = Depends(solo_plan_plus),
    sesion: Session = Depends(obtener_sesion),
):
    """La libreta de clientes del taller.

    Los archivados no van: quien exporta quiere su lista de hoy, no las fichas que borro.
    """
    encontrados = sesion.scalars(
        select(Client)
        .where(Client.workshop_id == usuario.workshop_id, Client.deleted_at.is_(None))
        .order_by(Client.name)
    ).all()

    return _archivo(
        "clientes.csv",
        ["Nombre", "Telefono", "RUT", "Notas", "Cliente desde"],
        [
            [
                cliente.name,
                cliente.phone,
                cliente.rut or "",
                cliente.notes or "",
                _fecha(cliente.created_at),
            ]
            for cliente in encontrados
        ],
    )


@router.get("/history", response_class=Response, responses=ARCHIVO_CSV)
def historial(
    usuario: User = Depends(solo_plan_plus),
    sesion: Session = Depends(obtener_sesion),
):
    """Todo lo que paso por el taller, una fila por orden.

    Va con la patente adelante porque es como se busca un auto: si el dueno abre esto en
    Excel, lo primero que hace es filtrar por una patente.
    """
    ordenes = sesion.scalars(
        select(Order)
        .where(Order.workshop_id == usuario.workshop_id, Order.deleted_at.is_(None))
        .order_by(Order.created_at.desc())
    ).all()

    return _archivo(
        "historial.csv",
        [
            "Patente", "Marca", "Modelo", "Cliente", "Telefono",
            "Trabajo", "Estado", "Ingreso", "Fecha estimada",
        ],
        [
            [
                orden.vehicle.plate,
                orden.vehicle.brand or "",
                orden.vehicle.model or "",
                orden.client.name,
                orden.client.phone,
                orden.title,
                ETIQUETAS_DE_ESTADO.get(orden.status, orden.status),
                _fecha(orden.created_at),
                _fecha(orden.estimated_at),
            ]
            for orden in ordenes
        ],
    )

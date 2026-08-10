"""El panel de Solve: dar de alta talleres, mirarlos y corregirlos.

Nada de aca toca los datos de un taller. Un admin de plataforma no ve ordenes, clientes
ni vehiculos: esos endpoints siguen filtrando por el taller del token, sin excepcion.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import ROL_ADMIN_PLATAFORMA, ROL_DUENO, Order, User, Workshop
from app.schemas.admin import (
    ClaveNueva,
    CuentaAdminEntrada,
    TallerEdicion,
    UsuarioAdminSalida,
)
from app.schemas.auth import AltaTallerEntrada, UserSalida, WorkshopSalida
from app.security.admin import exigir_clave_de_administracion
from app.security.dependencias import solo_admin_plataforma
from app.security.passwords import hashear
from app.services.altas import crear_taller_con_dueno

router = APIRouter(prefix="/admin", tags=["admin"])

TALLER_INTERNO = "Solve"


def _taller_interno(sesion: Session) -> Workshop:
    """El taller al que pertenecen las cuentas de Solve.

    `User.workshop_id` no admite nulos y `usuario_actual` exige que el taller este
    activo. Con un taller interno el admin entra por el mismo camino que todos y no
    hay que aflojar ni una linea del aislamiento.
    """
    taller = sesion.scalar(select(Workshop).where(Workshop.internal.is_(True)))
    if taller is None:
        taller = Workshop(name=TALLER_INTERNO, phone="000000000", internal=True)
        sesion.add(taller)
        sesion.flush()
    return taller


def _taller_o_404(sesion: Session, taller_id: str) -> Workshop:
    taller = sesion.scalar(
        select(Workshop).where(Workshop.id == taller_id, Workshop.internal.is_(False))
    )
    if taller is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")
    return taller


@router.post(
    "/accounts",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_clave_de_administracion)],
)
def crear_cuenta_de_admin(
    datos: CuentaAdminEntrada,
    sesion: Session = Depends(obtener_sesion),
):
    admin = User(
        workshop_id=_taller_interno(sesion).id,
        name=datos.name,
        email=datos.email,
        password_hash=hashear(datos.password),
        role=ROL_ADMIN_PLATAFORMA,
    )
    sesion.add(admin)
    sesion.commit()

    return {"data": UsuarioAdminSalida.model_validate(admin).model_dump(by_alias=True)}


@router.post("/workshops", status_code=status.HTTP_201_CREATED)
def crear_taller(
    datos: AltaTallerEntrada,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    taller, dueno = crear_taller_con_dueno(sesion, datos, creado_por=admin)
    sesion.commit()

    return {
        "data": {
            "workshop": WorkshopSalida.model_validate(taller).model_dump(by_alias=True),
            "owner": UserSalida.model_validate(dueno).model_dump(by_alias=True),
        }
    }


@router.get("/workshops", dependencies=[Depends(solo_admin_plataforma)])
def listar_talleres(sesion: Session = Depends(obtener_sesion)):
    """La lista sirve para una sola pregunta: quien esta usando esto de verdad.

    Por eso trae el conteo de ordenes y no solo los datos de contacto. Se arma con dos
    subconsultas correlacionadas y no con joins: un taller con dos duenos duplicaria filas.
    """
    correo_del_dueno = (
        select(User.email)
        .where(User.workshop_id == Workshop.id, User.role == ROL_DUENO)
        .order_by(User.created_at)
        .limit(1)
        .scalar_subquery()
    )
    ordenes = (
        select(func.count(Order.id))
        .where(Order.workshop_id == Workshop.id)
        .scalar_subquery()
    )

    filas = sesion.execute(
        select(Workshop, correo_del_dueno, ordenes)
        .where(Workshop.internal.is_(False))
        .order_by(Workshop.created_at.desc())
    ).all()

    return {
        "data": [
            {
                **WorkshopSalida.model_validate(taller).model_dump(by_alias=True),
                "ownerEmail": correo,
                "ordersCount": total,
            }
            for taller, correo, total in filas
        ]
    }


@router.patch("/workshops/{taller_id}", dependencies=[Depends(solo_admin_plataforma)])
def editar_taller(
    taller_id: str,
    datos: TallerEdicion,
    sesion: Session = Depends(obtener_sesion),
):
    taller = _taller_o_404(sesion, taller_id)

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        if valor is not None:
            setattr(taller, campo, valor)
    sesion.commit()

    return {"data": WorkshopSalida.model_validate(taller).model_dump(by_alias=True)}


@router.post(
    "/workshops/{taller_id}/owner-password",
    dependencies=[Depends(solo_admin_plataforma)],
)
def cambiar_clave_del_dueno(
    taller_id: str,
    datos: ClaveNueva,
    sesion: Session = Depends(obtener_sesion),
):
    """Para el dueno que perdio su clave. Sin esto, la unica salida es crearle otra
    cuenta -y ahi pierde sus ordenes, sus clientes y su historial por patente."""
    taller = _taller_o_404(sesion, taller_id)

    dueno = sesion.scalar(
        select(User)
        .where(User.workshop_id == taller.id, User.role == ROL_DUENO)
        .order_by(User.created_at)
    )
    if dueno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ese taller no tiene dueno"
        )

    dueno.password_hash = hashear(datos.password)
    sesion.commit()

    return {"data": UsuarioAdminSalida.model_validate(dueno).model_dump(by_alias=True)}

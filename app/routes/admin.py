"""El panel de Solve: dar de alta talleres, mirarlos y corregirlos.

Nada de aca toca los datos de un taller. Un admin de plataforma no ve ordenes, clientes
ni vehiculos: esos endpoints siguen filtrando por el taller del token, sin excepcion.

Las cuentas de admin NO se crean por aca. Se crean con `scripts/crear_admin.py`, en la
consola del servidor: una ruta HTTP que crea la cuenta mas poderosa del sistema es una
puerta abierta a internet, y la llave del servidor no alcanza para sostenerla.

Todo lo que el admin hace sobre un taller queda registrado en `admin_audit`.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import (
    ACCION_CLAVE_DEL_DUENO_CAMBIADA,
    ACCION_TALLER_CREADO,
    ACCION_TALLER_EDITADO,
    ACCION_TALLER_REACTIVADO,
    ACCION_TALLER_SUSPENDIDO,
    ROL_DUENO,
    AdminAudit,
    Order,
    User,
    Workshop,
)
from app.schemas.admin import ClaveNueva, TallerEdicion, UsuarioAdminSalida
from app.schemas.auth import AltaTallerEntrada, UserSalida, WorkshopSalida
from app.security.dependencias import solo_admin_plataforma
from app.security.passwords import hashear
from app.services.altas import crear_taller_con_dueno

router = APIRouter(prefix="/admin", tags=["admin"])


def _anotar(
    sesion: Session,
    admin: User,
    accion: str,
    taller_id: str | None = None,
    usuario_id: str | None = None,
    detalle: str | None = None,
) -> None:
    """Deja el rastro de lo que hizo el admin. Se llama antes del commit de la accion."""
    sesion.add(
        AdminAudit(
            actor_user_id=admin.id,
            action=accion,
            workshop_id=taller_id,
            target_user_id=usuario_id,
            detail=detalle,
        )
    )


def _taller_o_404(sesion: Session, taller_id: str) -> Workshop:
    taller = sesion.scalar(
        select(Workshop).where(Workshop.id == taller_id, Workshop.internal.is_(False))
    )
    if taller is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")
    return taller


@router.post("/workshops", status_code=status.HTTP_201_CREATED)
def crear_taller(
    datos: AltaTallerEntrada,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    taller, dueno = crear_taller_con_dueno(sesion, datos, creado_por=admin)
    _anotar(sesion, admin, ACCION_TALLER_CREADO, taller_id=taller.id, usuario_id=dueno.id)
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


@router.patch("/workshops/{taller_id}")
def editar_taller(
    taller_id: str,
    datos: TallerEdicion,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    taller = _taller_o_404(sesion, taller_id)

    cambios = {
        campo: valor
        for campo, valor in datos.model_dump(exclude_unset=True).items()
        if valor is not None
    }
    for campo, valor in cambios.items():
        setattr(taller, campo, valor)

    # La suspension no es "una edicion mas": deja a un taller entero sin poder entrar.
    # Merece su propia linea en el registro, que es lo que se lee cuando alguien
    # pregunta por que no puede trabajar.
    if "active" in cambios:
        _anotar(
            sesion,
            admin,
            ACCION_TALLER_SUSPENDIDO if not cambios["active"] else ACCION_TALLER_REACTIVADO,
            taller_id=taller.id,
        )

    otros = sorted(campo for campo in cambios if campo != "active")
    if otros:
        _anotar(
            sesion,
            admin,
            ACCION_TALLER_EDITADO,
            taller_id=taller.id,
            detalle=", ".join(otros),
        )
    sesion.commit()

    return {"data": WorkshopSalida.model_validate(taller).model_dump(by_alias=True)}


@router.post("/workshops/{taller_id}/owner-password")
def cambiar_clave_del_dueno(
    taller_id: str,
    datos: ClaveNueva,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    """Para el dueno que perdio su clave. Sin esto, la unica salida es crearle otra
    cuenta -y ahi pierde sus ordenes, sus clientes y su historial por patente.

    Es la accion mas delicada del panel: deja a una persona fuera de su propio sistema
    sin avisarle. Por eso queda anotada en `admin_audit` con nombre y apellido.
    """
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
    # Cambiar la clave tiene que cortar lo que ya estaba abierto: si no, quien tuviera
    # el token de antes sigue adentro hasta 12 horas mas, con la clave vieja inservible.
    dueno.token_version += 1
    _anotar(
        sesion,
        admin,
        ACCION_CLAVE_DEL_DUENO_CAMBIADA,
        taller_id=taller.id,
        usuario_id=dueno.id,
    )
    sesion.commit()

    return {"data": UsuarioAdminSalida.model_validate(dueno).model_dump(by_alias=True)}

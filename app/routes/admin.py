"""El panel de Solve: dar de alta talleres, mirarlos, corregirlos y suspenderlos.

Nada de aca toca los datos de un taller: este archivo administra la cuenta, no el trabajo.
`/orders`, `/clients` y `/vehicles` siguen filtrando por el taller del token, sin
excepcion, y un admin que los pida recibe la lista vacia de su propio taller interno.

Para mirar lo que un taller tiene entre manos -cuando llaman con un problema- existe
`app/routes/admin_soporte.py`, que es otra puerta: solo lectura y anotada.

La PRIMERA cuenta de administracion se crea con `scripts/crear_admin.py`, en la consola
del servidor. Las siguientes se crean aca, pero con la sesion de un admin que ya entro:
lo que se borro fue la ruta que las creaba con una llave suelta, sin nadie identificable
detras. Todo lo que hace el admin queda registrado en `admin_audit`.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import (
    ACCION_CLAVE_DEL_DUENO_CAMBIADA,
    ACCION_CUENTA_ADMIN_CREADA,
    ACCION_CUENTA_ADMIN_EDITADA,
    ACCION_TALLER_CREADO,
    ACCION_TALLER_DADO_DE_BAJA,
    ACCION_TALLER_EDITADO,
    ACCION_TALLER_REACTIVADO,
    ACCION_TALLER_RESTAURADO,
    ACCION_TALLER_SUSPENDIDO,
    ACCION_USUARIO_CREADO,
    ROL_ADMIN_PLATAFORMA,
    ROL_DUENO,
    ROL_MECANICO,
    AdminAudit,
    Order,
    User,
    Workshop,
)
from app.models.base import ahora
from app.schemas.admin import (
    ClaveNueva,
    CuentaAdminEdicion,
    CuentaAdminEntrada,
    TallerEdicion,
    UsuarioAdminSalida,
)
from app.schemas.auth import AltaTallerEntrada, UserSalida, WorkshopSalida
from app.schemas.user import UsuarioDeRespaldoEntrada, UsuarioSalida
from app.security.dependencias import solo_admin_plataforma
from app.security.passwords import hashear
from app.services.altas import correo_libre, crear_admin, crear_taller_con_dueno
from app.services.planes import verificar_cupo

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


def taller_del_panel(
    sesion: Session, taller_id: str, incluir_dados_de_baja: bool = False
) -> Workshop:
    """El taller del panel. Nunca el interno de Solve: ese no se administra desde aca.

    Sin guion bajo porque la vista de soporte (`app/routes/admin_soporte.py`) entra por
    la misma puerta: si mirar un taller usara otra busqueda, el taller interno de Solve
    terminaria siendo visible por un lado y no por el otro.

    Por defecto ignora los dados de baja, para que una peticion vieja no reviva sin
    querer un taller que ya se fue. Solo `restore` pide verlos.
    """
    condiciones = [Workshop.id == taller_id, Workshop.internal.is_(False)]
    if not incluir_dados_de_baja:
        condiciones.append(Workshop.deleted_at.is_(None))

    taller = sesion.scalar(select(Workshop).where(*condiciones))
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
def listar_talleres(
    archived: bool = Query(default=False),
    sesion: Session = Depends(obtener_sesion),
):
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

    condiciones = [Workshop.internal.is_(False)]
    # Los suspendidos si salen: son los que se van a reactivar. Los dados de baja no,
    # salvo que se pidan, para que la lista responda "quien esta usando esto" y no
    # "quien lo uso alguna vez".
    condiciones.append(
        Workshop.deleted_at.is_not(None) if archived else Workshop.deleted_at.is_(None)
    )

    filas = sesion.execute(
        select(Workshop, correo_del_dueno, ordenes)
        .where(*condiciones)
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
    taller = taller_del_panel(sesion, taller_id)

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
    taller = taller_del_panel(sesion, taller_id)

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


@router.delete("/workshops/{taller_id}", status_code=status.HTTP_204_NO_CONTENT)
def dar_de_baja(
    taller_id: str,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    """El taller se fue. Sale de la lista y nadie de ahi entra, pero no se borra nada.

    Sus ordenes, sus clientes y su historial por patente quedan enteros: si vuelve en dos
    meses, `restore` le devuelve todo donde lo dejo. Es la misma decision que con los
    clientes y las ordenes, y por la misma razon.
    """
    taller = taller_del_panel(sesion, taller_id, incluir_dados_de_baja=True)

    # Repetirlo no mueve la fecha original: es la respuesta a "cuando se fue".
    if taller.deleted_at is None:
        taller.deleted_at = ahora()
        taller.active = False
        _anotar(sesion, admin, ACCION_TALLER_DADO_DE_BAJA, taller_id=taller.id)
        sesion.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/workshops/{taller_id}/restore")
def restaurar(
    taller_id: str,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    """Devuelve a la vida un taller dado de baja, con todo lo suyo adentro.

    Pedir lo que ya se cumple no es un error: sobre un taller vigente lo deja activo y
    responde igual, para que el panel pueda reintentar sin miedo.
    """
    taller = taller_del_panel(sesion, taller_id, incluir_dados_de_baja=True)

    if taller.deleted_at is not None or not taller.active:
        taller.deleted_at = None
        taller.active = True
        # Tambien se borra la fecha de termino: si quedara escrita, el taller volveria
        # con una suspension agendada que ya nadie recuerda.
        taller.suspended_until = None
        _anotar(sesion, admin, ACCION_TALLER_RESTAURADO, taller_id=taller.id)
        sesion.commit()

    return {"data": WorkshopSalida.model_validate(taller).model_dump(by_alias=True)}


@router.get("/workshops/{taller_id}/users", dependencies=[Depends(solo_admin_plataforma)])
def equipo_del_taller(taller_id: str, sesion: Session = Depends(obtener_sesion)):
    """Ver quien trabaja en un taller. Es lo que se mira antes de ayudar por telefono."""
    taller = taller_del_panel(sesion, taller_id, incluir_dados_de_baja=True)

    equipo = sesion.scalars(
        select(User).where(User.workshop_id == taller.id).order_by(User.created_at)
    ).all()

    return {
        "data": [
            UsuarioSalida.model_validate(usuario).model_dump(by_alias=True)
            for usuario in equipo
        ]
    }


@router.post("/workshops/{taller_id}/users", status_code=status.HTTP_201_CREATED)
def crear_usuario_de_respaldo(
    taller_id: str,
    datos: UsuarioDeRespaldoEntrada,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    """La puerta de respaldo: crear una cuenta dentro de un taller que no es de Solve.

    Existe para el dueno que se perdio o que perdio a su unico dueno activo. Como es
    entrar en la casa de otro, queda anotada en `admin_audit` con nombre y apellido.
    """
    taller = taller_del_panel(sesion, taller_id)

    # El tope es del taller y no de quien lo pide: si Solve necesita pasarse, primero sube
    # el plan, y ese cambio queda anotado. Un dueno de repuesto nunca se bloquea: el tope
    # es de mecanicos, y esta es la unica puerta que queda cuando adentro no hay nadie
    # que pueda administrar.
    if datos.role == ROL_MECANICO:
        verificar_cupo(sesion, taller)

    usuario = User(
        workshop_id=taller.id,
        name=datos.name,
        email=correo_libre(sesion, datos.email),
        password_hash=hashear(datos.password),
        role=datos.role,
    )
    sesion.add(usuario)
    sesion.flush()
    _anotar(
        sesion,
        admin,
        ACCION_USUARIO_CREADO,
        taller_id=taller.id,
        usuario_id=usuario.id,
        detalle=datos.role,
    )
    sesion.commit()

    return {"data": UsuarioSalida.model_validate(usuario).model_dump(by_alias=True)}


@router.post("/accounts", status_code=status.HTTP_201_CREATED)
def crear_cuenta_de_admin(
    datos: CuentaAdminEntrada,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    """La segunda cuenta de Solve y las que sigan.

    No resucita la ruta que se borro: aquella pedia una llave que viajaba por internet y
    creaba la cuenta mas poderosa del sistema sin dejar rastro de quien lo hizo. Esta
    exige una sesion de administrador, asi que hay una persona identificable detras y
    queda anotada. La primera cuenta sigue naciendo en la consola del servidor.

    `crear_admin` levanta sus fallas como HTTPException, asi que aca no se traduce nada.
    """
    nuevo = crear_admin(sesion, datos.name, datos.email, datos.password)

    sesion.flush()
    _anotar(sesion, admin, ACCION_CUENTA_ADMIN_CREADA, usuario_id=nuevo.id)
    sesion.commit()

    return {"data": UsuarioAdminSalida.model_validate(nuevo).model_dump(by_alias=True)}


@router.get("/accounts", dependencies=[Depends(solo_admin_plataforma)])
def listar_cuentas_de_admin(sesion: Session = Depends(obtener_sesion)):
    """Quien tiene las llaves del panel. Se mira antes de crear otra o apagar una."""
    cuentas = sesion.scalars(
        select(User)
        .where(User.role == ROL_ADMIN_PLATAFORMA)
        .order_by(User.created_at)
    ).all()

    return {
        "data": [
            UsuarioAdminSalida.model_validate(cuenta).model_dump(by_alias=True)
            for cuenta in cuentas
        ]
    }


@router.patch("/accounts/{cuenta_id}")
def editar_cuenta_de_admin(
    cuenta_id: str,
    datos: CuentaAdminEdicion,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    """Apagar o renombrar una cuenta de Solve.

    Nunca la ultima activa, y nunca la propia: quedarse sin ninguna cuenta de plataforma
    deja el panel cerrado para todos, y la unica salida seria volver a la consola del
    servidor.
    """
    cuenta = sesion.scalar(
        select(User).where(User.id == cuenta_id, User.role == ROL_ADMIN_PLATAFORMA)
    )
    if cuenta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

    cambios = datos.model_dump(exclude_unset=True)
    # Igual que con el equipo del taller: quien pide esto es un admin activo, asi que
    # apagando a otro siempre queda al menos uno. Prohibir apagarse a si mismo es lo
    # unico que hace falta para que el panel no quede cerrado para todos.
    if cambios.get("active") is False and cuenta.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes desactivar tu propia cuenta",
        )

    for campo, valor in cambios.items():
        if valor is not None:
            setattr(cuenta, campo, valor)
    _anotar(sesion, admin, ACCION_CUENTA_ADMIN_EDITADA, usuario_id=cuenta.id)
    sesion.commit()

    return {"data": UsuarioAdminSalida.model_validate(cuenta).model_dump(by_alias=True)}

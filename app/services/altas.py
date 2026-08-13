"""Dar de alta talleres, duenos y cuentas de administracion.

Vive aca y no dentro de una ruta porque a cada alta se entra por dos puertas: al taller,
por `/auth/register` con la clave del servidor -la de emergencia- y por el panel de admin
con la cuenta de cada uno; a la cuenta de plataforma, por la consola del servidor y por
`POST /admin/accounts`. Si el alta estuviera escrita en cada puerta, se irian separando:
una validaria algo que la otra no.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ROL_ADMIN_PLATAFORMA, ROL_DUENO, User, Workshop
from app.schemas.auth import AltaTallerEntrada
from app.security.passwords import hashear

TALLER_INTERNO = "Solve"

LARGO_MINIMO_DE_CLAVE_ADMIN = 12


def correo_libre(sesion: Session, email: str) -> str:
    """Deja el correo listo para guardar, o levanta 409 si ya esta tomado.

    Normaliza antes de comparar: el correo es unico en todo el sistema y es con lo que se
    entra, sin tener que elegir taller. Si una puerta guardara "Ana@taller.cl" y otra
    buscara "ana@taller.cl", el mismo correo entraria dos veces y el login dejaria de
    saber a quien se refiere.
    """
    email = email.strip().lower()
    if sesion.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo",
        )
    return email


def taller_interno(sesion: Session) -> Workshop:
    """El taller al que pertenecen las cuentas de la administracion de la plataforma.

    `User.workshop_id` no admite nulos y `usuario_actual` exige que el taller este
    activo. Con un taller interno el admin entra por el mismo camino que todos y no hay
    que aflojar ni una linea del aislamiento entre talleres.
    """
    taller = sesion.scalar(select(Workshop).where(Workshop.internal.is_(True)))
    if taller is None:
        taller = Workshop(name=TALLER_INTERNO, phone="56900000000", internal=True)
        sesion.add(taller)
        sesion.flush()
    return taller


def crear_taller_con_dueno(
    sesion: Session, datos: AltaTallerEntrada, creado_por: User | None = None
) -> tuple[Workshop, User]:
    """Deja el taller y su dueno listos para entrar. No hace commit: decide quien llama.

    `creado_por` queda anotado en el taller: es lo que permite saber quien dio de alta a
    quien. Va vacio cuando el alta entra por `/auth/register`, que no tiene una persona
    detras sino la clave del servidor.

    Levanta 409 si el correo ya existe. Se comprueba ANTES de crear el taller: sin este
    chequeo el alta reventaria a mitad de camino, con el taller ya creado y sin dueno.
    """
    email = correo_libre(sesion, datos.email)

    taller = Workshop(
        name=datos.workshop_name,
        phone=datos.workshop_phone,
        plan=datos.plan,
        created_by_user_id=creado_por.id if creado_por else None,
    )
    sesion.add(taller)
    sesion.flush()

    dueno = User(
        workshop_id=taller.id,
        name=datos.owner_name,
        email=email,
        password_hash=hashear(datos.password),
        role=ROL_DUENO,
    )
    sesion.add(dueno)
    return taller, dueno


def crear_admin(sesion: Session, nombre: str, email: str, clave: str) -> User:
    """Una cuenta de administracion de la plataforma. No hace commit.

    Vive aca y no en el script porque se entra por dos puertas: la consola del servidor
    para la primera cuenta -cuando todavia no hay ninguna sesion posible- y
    `POST /admin/accounts` para las siguientes, ya con un admin identificable detras.

    La clave se exige mas larga que la de cualquier otra cuenta a proposito: con esta se
    da de alta talleres y se le cambia la clave al dueno de cualquiera de ellos.

    Las dos fallas posibles -correo tomado y clave corta- salen como `HTTPException`, la
    misma moneda que usa `crear_taller_con_dueno`. Asi la ruta no tiene que traducir nada
    y el script traduce una sola vez, en un solo lugar.
    """
    if len(clave) < LARGO_MINIMO_DE_CLAVE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"La clave necesita al menos {LARGO_MINIMO_DE_CLAVE_ADMIN} caracteres: "
                "es la cuenta con mas poder del sistema."
            ),
        )

    admin = User(
        workshop_id=taller_interno(sesion).id,
        name=nombre.strip(),
        email=correo_libre(sesion, email),
        password_hash=hashear(clave),
        role=ROL_ADMIN_PLATAFORMA,
    )
    sesion.add(admin)
    return admin

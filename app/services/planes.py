"""Que le deja hacer al taller el plan que paga.

Hoy es una sola cosa: cuanta gente puede tener trabajando. Vive aca y no dentro de una
ruta porque a ocupar un cupo se entra por tres puertas -el dueno contratando por `/users`,
Solve por la puerta de respaldo, y el interruptor que vuelve a encender a alguien que
estaba apagado-. Escrita en cada una, la cuenta se iria separando: una contaria a los
apagados y la otra no.
"""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import MAX_MECANICOS_BASICO, PLAN_BASICO, ROL_MECANICO, User, Workshop

# Solo el plan chico tiene tope. El que no esta aca no lo tiene.
TOPE_DE_MECANICOS = {PLAN_BASICO: MAX_MECANICOS_BASICO}


def mecanicos_activos(sesion: Session, workshop_id: str) -> int:
    """Los que estan trabajando hoy.

    El dueno no cuenta -la landing vende "1 cuenta dueno + hasta 3 mecanicos"- y los
    apagados tampoco: el taller que despidio a uno no arrastra su cupo para siempre.
    """
    return sesion.scalar(
        select(func.count(User.id)).where(
            User.workshop_id == workshop_id,
            User.role == ROL_MECANICO,
            User.active.is_(True),
        )
    )


def verificar_cupo(sesion: Session, taller: Workshop) -> None:
    """Levanta 409 si sumar un mecanico mas se pasa del plan.

    Se pregunta al agregar y al reactivar, **nunca hacia atras**: un taller que ya tiene
    mas de los que caben -porque se paso al plan chico- no pierde a nadie ni deja de
    entrar. Lo unico que no puede es sumar al siguiente. Bajar de plan no puede botar a
    alguien que esta trabajando.
    """
    tope = TOPE_DE_MECANICOS.get(taller.plan)
    if tope is None:
        return

    if mecanicos_activos(sesion, taller.id) >= tope:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El plan {taller.plan} permite hasta {tope} mecanicos activos. "
                "Para sumar mas, el taller pasa a Plus."
            ),
        )

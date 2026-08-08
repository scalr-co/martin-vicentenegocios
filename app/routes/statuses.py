"""Los estados por los que pasa una orden, para que el frontend no los escriba a mano."""

from fastapi import APIRouter, Depends

from app.models import ESTADO_CERRADO, ESTADOS, User
from app.security.dependencias import usuario_actual
from app.services.presentacion import ETIQUETAS_DE_ESTADO

router = APIRouter(prefix="/statuses", tags=["statuses"])


@router.get("")
def listar(usuario: User = Depends(usuario_actual)):
    return {
        "data": [
            {
                "key": estado,
                "label": ETIQUETAS_DE_ESTADO[estado],
                # Las abiertas son las que el taller todavia tiene entre manos.
                "isOpen": estado != ESTADO_CERRADO,
            }
            for estado in ESTADOS
        ]
    }

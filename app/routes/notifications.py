"""Avisos al cliente.

El backend los deja escritos y en `link_ready`. Quien sabe si de verdad salieron es el
frontend, cuando el mecanico aprieta el boton de WhatsApp: por eso los marca aca.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import AVISO_ENVIADO, Notification, User
from app.models.base import ahora
from app.schemas.order import AvisoEnviado, AvisoSalida
from app.security.dependencias import usuario_actual

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/{aviso_id}/sent")
def marcar_como_enviado(
    aviso_id: str,
    datos: AvisoEnviado | None = None,
    usuario: User = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    aviso = sesion.scalar(
        select(Notification).where(
            Notification.id == aviso_id,
            Notification.workshop_id == usuario.workshop_id,
        )
    )
    if aviso is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso no encontrado")

    # El envio ocurrio una sola vez: si ya estaba marcado, la hora original se respeta,
    # y el texto que el cliente ya leyo tampoco se puede reescribir despues.
    if aviso.status != AVISO_ENVIADO:
        if datos is not None and datos.message is not None:
            # El mecanico cambio el borrador antes de mandarlo: se guarda lo que salio.
            aviso.message = datos.message
        aviso.status = AVISO_ENVIADO
        aviso.sent_at = ahora()
        sesion.commit()

    return {"data": AvisoSalida.model_validate(aviso).model_dump(by_alias=True, mode="json")}

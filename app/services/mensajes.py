"""Lo que se le escribe al cliente en cada estado.

Son borradores, no textos finales: el mecanico los ve antes de enviar y puede
reemplazarlos cuando hay algo que la plantilla no puede adivinar —una fuga que aparecio
al desarmar, un repuesto que no llego—. Por eso el aviso se guarda despues de que el
mecanico decide, y se guarda el texto que de verdad salio.
"""

from app.models.order import (
    ESTADO_EN_DIAGNOSTICO,
    ESTADO_EN_REPARACION,
    ESTADO_ENTREGADO,
    ESTADO_ESPERANDO_APROBACION,
    ESTADO_ESPERANDO_REPUESTO,
    ESTADO_LISTO,
    ESTADO_RECIBIDO,
)
from app.services.presentacion import describir_para_el_cliente, primer_nombre

PLANTILLAS = {
    ESTADO_RECIBIDO: (
        "Hola {nombre}, recibimos tu {vehiculo} en {taller}. "
        "Te vamos avisando cómo avanza."
    ),
    ESTADO_EN_DIAGNOSTICO: (
        "Hola {nombre}, ya estamos revisando tu {vehiculo} para ver qué tiene. "
        "Te contamos apenas sepamos."
    ),
    ESTADO_ESPERANDO_APROBACION: (
        "Hola {nombre}, terminamos de revisar tu {vehiculo} y te preparamos el "
        "presupuesto. Nos confirmas y seguimos."
    ),
    ESTADO_EN_REPARACION: (
        "Hola {nombre}, ya estamos trabajando en tu {vehiculo}."
    ),
    ESTADO_ESPERANDO_REPUESTO: (
        "Hola {nombre}, tu {vehiculo} está esperando un repuesto. "
        "Apenas llegue seguimos y te avisamos."
    ),
    ESTADO_LISTO: (
        "Hola {nombre}, tu {vehiculo} ya está listo para retirar en {taller}."
    ),
    ESTADO_ENTREGADO: (
        "Hola {nombre}, gracias por confiar en {taller}. "
        "Cualquier cosa con tu {vehiculo}, nos escribes."
    ),
}


def mensaje_para(
    estado: str,
    *,
    nombre_cliente: str,
    patente: str,
    marca: str | None,
    modelo: str | None,
    nombre_taller: str,
) -> str:
    """El borrador del aviso para ese estado, ya con los datos del cliente adentro."""
    plantilla = PLANTILLAS[estado]
    return plantilla.format(
        nombre=primer_nombre(nombre_cliente),
        vehiculo=describir_para_el_cliente(patente, marca, modelo),
        taller=nombre_taller,
    )

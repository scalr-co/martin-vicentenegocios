"""Como se escribe un vehiculo cuando hay que mostrarlo.

Vive aca y no en cada pantalla para que el texto que ve el mecanico y el que le llega al
cliente por WhatsApp salgan del mismo lugar y no se vayan separando con el tiempo.
"""


# Marcas que no se escriben con una sola mayuscula inicial. Sin esta lista, "bmw"
# terminaria como "Bmw", que se lee peor que no haber corregido nada.
MARCAS_EN_MAYUSCULAS = {"bmw", "mg", "jac", "byd", "dfsk", "gac", "jmc", "ram", "vw"}


def con_mayuscula_inicial(texto: str) -> str:
    """Solo la primera letra. No usa `.capitalize()` para no aplastar "SsangYong"."""
    return texto[:1].upper() + texto[1:]


def _marca_presentable(marca: str) -> str:
    if marca.lower() in MARCAS_EN_MAYUSCULAS:
        return marca.upper()
    return con_mayuscula_inicial(marca)


def _marca_y_modelo(marca: str | None, modelo: str | None) -> str:
    """El modelo se deja tal cual lo escribio el mecanico.

    No hay regla que sirva para CX-5, RAV4 e i10 al mismo tiempo: `.title()` los
    convertiria en "Cx-5", "Rav4" e "I10". Corregido y equivocado se ve peor que
    tal como lo escribieron, porque el cliente duda de si el taller sabe que auto tiene.
    """
    partes = [_marca_presentable(marca)] if marca else []
    if modelo:
        partes.append(modelo)
    return " ".join(partes)


def describir_vehiculo(patente: str, marca: str | None, modelo: str | None) -> str:
    """"Toyota Corolla · Patente ABCD12", o solo la patente si no se anoto mas."""
    descripcion = _marca_y_modelo(marca, modelo)
    if not descripcion:
        return f"Patente {patente}"
    return f"{descripcion} · Patente {patente}"


def describir_para_el_cliente(patente: str, marca: str | None, modelo: str | None) -> str:
    """Como se lo nombra a su dueno, que ya sabe cual es: "Toyota Corolla (ABCD12)".

    Se completa con "tu" adelante en los mensajes, por eso no lo trae.
    """
    descripcion = _marca_y_modelo(marca, modelo)
    if not descripcion:
        # Con tilde: esto lo lee el cliente del taller por WhatsApp.
        return f"vehículo (patente {patente})"
    return f"{descripcion} ({patente})"


"""Como se escribe cada estado en pantalla.

Vive junto al resto de la presentacion y se sirve por `GET /statuses`, para que el
frontend no tenga que escribir los estados a mano y quedarse viejo cuando cambien.
"""
ETIQUETAS_DE_ESTADO = {
    "recibido": "Recibido",
    "en_diagnostico": "En diagnóstico",
    "esperando_aprobacion": "Esperando aprobación",
    "en_reparacion": "En reparación",
    "esperando_repuesto": "Esperando repuesto",
    "listo": "Listo",
    "entregado": "Entregado",
}


def primer_nombre(nombre_completo: str) -> str:
    """Al cliente se le habla por su nombre, no por su nombre y sus dos apellidos.

    Va con mayuscula inicial aunque la ficha diga "juan": el mecanico escribe rapido y
    el cliente no tiene por que enterarse. Las tildes no se inventan -de "perez" no se
    puede deducir si es "Perez" o "Perez"- porque escribir mal un apellido es peor.

    Si la ficha viene con coma, esta escrita como en un formulario -"Munoz, Juan"- y el
    nombre esta despues. Sin esto el mensaje partia con "Hola Munoz".
    """
    texto = nombre_completo.strip()
    if "," in texto:
        texto = texto.split(",", 1)[1].strip() or texto

    partes = texto.split()
    if not partes:
        return nombre_completo
    return con_mayuscula_inicial(partes[0])

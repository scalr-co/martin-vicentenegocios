"""Como se escribe un vehiculo cuando hay que mostrarlo.

Vive aca y no en cada pantalla para que el texto que ve el mecanico y el que le llega al
cliente por WhatsApp salgan del mismo lugar y no se vayan separando con el tiempo.
"""


def describir_vehiculo(patente: str, marca: str | None, modelo: str | None) -> str:
    """"Toyota Corolla · Patente ABCD12", o solo la patente si no se anoto mas."""
    descripcion = " ".join(parte for parte in (marca, modelo) if parte)
    if not descripcion:
        return f"Patente {patente}"
    return f"{descripcion} · Patente {patente}"


def describir_para_el_cliente(patente: str, marca: str | None, modelo: str | None) -> str:
    """Como se lo nombra a su dueno, que ya sabe cual es: "Toyota Corolla (ABCD12)".

    Se completa con "tu" adelante en los mensajes, por eso no lo trae.
    """
    descripcion = " ".join(parte for parte in (marca, modelo) if parte)
    if not descripcion:
        return f"vehiculo (patente {patente})"
    return f"{descripcion} ({patente})"


def primer_nombre(nombre_completo: str) -> str:
    """Al cliente se le habla por su nombre, no por su nombre y sus dos apellidos."""
    partes = nombre_completo.strip().split()
    return partes[0] if partes else nombre_completo

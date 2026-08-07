from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class Esquema(BaseModel):
    """Padre de todos los esquemas de entrada y salida.

    Por dentro escribimos en espanol con guion bajo (whatsapp_mode) y hacia afuera
    sale en el formato que espera el frontend (whatsappMode).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

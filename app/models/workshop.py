from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import ahora, nuevo_id

ESTADO_ACTIVO = "active"
ESTADO_SUSPENDIDO = "suspended"
ESTADO_DADO_DE_BAJA = "deleted"


def con_huso(fecha: datetime) -> datetime:
    """La misma fecha, siempre comparable.

    SQLite devuelve las fechas sin huso aunque la columna sea DateTime(timezone=True).
    Comparada a secas contra un datetime con huso, Python levanta TypeError y la puerta
    de entrada responde 500 a todo el taller. Lo que viene sin huso se lee como UTC, que
    es como se guardo.
    """
    return fecha.replace(tzinfo=UTC) if fecha.tzinfo is None else fecha

MODO_LINK = "link"
MODO_API = "api"

# Los dos planes que se venden en la landing. El basico trae hasta tres mecanicos; el
# plus no tiene tope. El numero es el mismo de `frontend/src/lib/plans.ts`, pero el que
# manda es este: un tope que solo vive en el navegador no es un tope.
PLAN_BASICO = "basico"
PLAN_PLUS = "plus"
PLANES = (PLAN_BASICO, PLAN_PLUS)
MAX_MECANICOS_BASICO = 3


class Workshop(Base):
    """Un taller. Es la unidad de aislamiento: todo lo demas le pertenece a uno."""

    __tablename__ = "workshops"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=nuevo_id)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))

    # "link": el frontend abre wa.me y el mecanico aprieta enviar.
    # "api": envio automatico por Meta. Reservado, todavia sin implementar.
    whatsapp_mode: Mapped[str] = mapped_column(String(10), default=MODO_LINK)

    timezone: Mapped[str] = mapped_column(String(60), default="America/Santiago")

    # Que le da derecho a usar. Hoy decide cuantos mecanicos puede tener; manana, que
    # mas ve. Los talleres que ya existian quedaron en basico, que es lo que son.
    plan: Mapped[str] = mapped_column(String(10), default=PLAN_BASICO)

    # Permite suspender un taller sin borrarle los datos.
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Hasta cuando dura la suspension. Nulo con `active` en falso significa "hasta que
    # alguien lo reactive"; con fecha, el taller vuelve solo cuando esa fecha se cumple.
    # Se guarda la fecha y no un contador de dias porque lo que se acuerda con el taller
    # es un dia: "vuelves el 1 de septiembre".
    suspended_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    # El taller interno de Solve, donde viven las cuentas de administracion. No es un
    # taller mecanico: no aparece en la lista del panel.
    internal: Mapped[bool] = mapped_column(Boolean, default=False)

    # La baja definitiva: el taller se fue. Sale de la lista del panel y nadie de ahi
    # entra, pero sus ordenes, sus clientes y su historial por patente quedan enteros,
    # por si vuelve. Se guarda la fecha y no un booleano por lo mismo que en clientes:
    # cuando se pregunta por un taller que falta, lo que se quiere saber es cuando dejo
    # de estar.
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    # Que admin lo dio de alta. Nulo en los que se crearon antes del panel y en el
    # interno. `use_alter` porque users apunta a workshops y workshops apunta a users:
    # sin eso, SQLAlchemy no sabe cual tabla crear primero.
    created_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", use_alter=True), default=None
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    def puede_entrar(self, momento: datetime) -> bool:
        """Si la gente de este taller puede trabajar en este instante.

        Es la unica definicion de "esta activo" que hay en el sistema: la usa la puerta
        de entrada y la usa lo que muestra el panel. Escrita dos veces, un dia una diria
        que el taller entra y la otra lo mostraria suspendido.

        El orden importa: `dar_de_baja` tambien deja `active` en falso, asi que si la
        fecha se mirara primero, un taller que ya se fue volveria a entrar solo porque
        arrastraba una suspension vencida.
        """
        if self.deleted_at is not None:
            return False
        if self.active:
            return True
        if self.suspended_until is None:
            return False
        return momento >= con_huso(self.suspended_until)

    def estado(self, momento: datetime) -> str:
        """Las tres situaciones posibles, con los nombres que usa el panel."""
        if self.deleted_at is not None:
            return ESTADO_DADO_DE_BAJA
        return ESTADO_ACTIVO if self.puede_entrar(momento) else ESTADO_SUSPENDIDO

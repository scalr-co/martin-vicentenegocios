from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

CLAVE_DE_DESARROLLO = "desarrollo-inseguro-cambiar-en-produccion"
LARGO_MINIMO_DE_CLAVE = 32

# El driver de Postgres que instala este proyecto. Los proveedores de hosting entregan
# la URL sin decir el driver, y SQLAlchemy entonces asume psycopg2, que no esta instalado.
DRIVER_DE_POSTGRES = "postgresql+psycopg://"
PREFIJOS_DE_POSTGRES = ("postgresql://", "postgres://")


class ConfiguracionInvalida(Exception):
    """Falta una variable de entorno o trae un valor que no sirve para este entorno."""


class Settings(BaseSettings):
    """Configuracion leida del entorno. Un .env local, variables reales en produccion."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "desarrollo" o "produccion". En produccion las validaciones se ponen estrictas.
    entorno: str = "desarrollo"

    # Conexion a la base de datos. En desarrollo un archivo SQLite; en produccion, Postgres.
    database_url: str = "sqlite:///./motorping.db"

    # Dominios del frontend autorizados a llamar la API, separados por coma.
    frontend_origins: str = "http://localhost:3000"

    # Clave con que se firman los tokens de sesion.
    # El valor por defecto sirve solo para desarrollo y tests.
    jwt_secret: str = CLAVE_DE_DESARROLLO

    # Clave para dar de alta talleres. Vacia significa que el alta esta cerrada.
    admin_api_key: str = ""

    @field_validator("database_url")
    @classmethod
    def _con_el_driver_que_tenemos(cls, valor: str) -> str:
        """Deja la URL del hosting en la forma que este proyecto sabe abrir.

        Railway y compania entregan "postgresql://..." tal cual; si se usa asi, la
        aplicacion no levanta y el error habla de psycopg2, que no tiene nada que ver.
        """
        for prefijo in PREFIJOS_DE_POSTGRES:
            if valor.startswith(prefijo):
                return DRIVER_DE_POSTGRES + valor[len(prefijo) :]
        return valor

    @property
    def es_produccion(self) -> bool:
        return self.entorno == "produccion"

    @property
    def origenes_permitidos(self) -> list[str]:
        return [origen.strip() for origen in self.frontend_origins.split(",") if origen.strip()]

    @model_validator(mode="after")
    def revisar_para_produccion(self) -> "Settings":
        if not self.es_produccion:
            return self

        if self.jwt_secret == CLAVE_DE_DESARROLLO:
            raise ConfiguracionInvalida(
                "JWT_SECRET sigue siendo la clave de desarrollo, que esta publicada en el "
                "repositorio. Genera una propia antes de desplegar."
            )
        if len(self.jwt_secret) < LARGO_MINIMO_DE_CLAVE:
            raise ConfiguracionInvalida(
                f"JWT_SECRET es demasiado corta: necesita al menos {LARGO_MINIMO_DE_CLAVE} "
                "caracteres para firmar de forma segura."
            )
        if self.admin_api_key and len(self.admin_api_key) < LARGO_MINIMO_DE_CLAVE:
            # Vacia esta bien: significa que el alta por HTTP esta cerrada. Lo que no
            # puede pasar es que este puesta y sea corta: con ella se dan de alta
            # talleres, y hasta hoy cualquier valor no vacio servia.
            raise ConfiguracionInvalida(
                f"ADMIN_API_KEY es demasiado corta: necesita al menos "
                f"{LARGO_MINIMO_DE_CLAVE} caracteres, o dejarla vacia para cerrar el alta."
            )
        return self


settings = Settings()

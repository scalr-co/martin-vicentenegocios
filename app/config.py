from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

CLAVE_DE_DESARROLLO = "desarrollo-inseguro-cambiar-en-produccion"
LARGO_MINIMO_DE_CLAVE = 32


class ConfiguracionInvalida(Exception):
    """Falta una variable de entorno o trae un valor que no sirve para este entorno."""


class Settings(BaseSettings):
    """Configuracion leida del entorno. Un .env local, variables reales en produccion."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "desarrollo" o "produccion". En produccion las validaciones se ponen estrictas.
    entorno: str = "desarrollo"

    # Conexion a la base de datos. En desarrollo un archivo SQLite; en produccion, Postgres.
    database_url: str = "sqlite:///./tallertrack.db"

    # Dominios del frontend autorizados a llamar la API, separados por coma.
    frontend_origins: str = "http://localhost:3000"

    # Clave con que se firman los tokens de sesion.
    # El valor por defecto sirve solo para desarrollo y tests.
    jwt_secret: str = CLAVE_DE_DESARROLLO

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
        return self


settings = Settings()

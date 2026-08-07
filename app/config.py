from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion leida del entorno. Un .env local, variables reales en produccion."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Dominios del frontend autorizados a llamar la API, separados por coma.
    frontend_origins: str = "http://localhost:3000"

    @property
    def origenes_permitidos(self) -> list[str]:
        return [origen.strip() for origen in self.frontend_origins.split(",") if origen.strip()]


settings = Settings()

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


CookieSameSite = Literal["lax", "strict", "none"]


class Settings(BaseSettings):
    ENV: str = "development"
    OPENROUTER_API_KEY: str = "unknown"
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash"
    OPENROUTER_SITE_URL: str = ""
    OPENROUTER_APP_TITLE: str = "EasyVocab"
    OPENROUTER_TIMEOUT_SECONDS: int = 20
    OPENROUTER_MAX_RETRIES: int = 2
    OPENROUTER_FALLBACK_MODELS: list[str] = ["google/gemini-2.5-pro"]

    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "unknown"
    POSTGRES_DB: str = "app"
    POSTGRES_PORT: int = 5432

    SECRET_KEY: str = "dev_secret_key_change_me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    SESSION_COOKIE_NAME: str = "session"
    COOKIE_SECURE: bool | None = None
    COOKIE_SAMESITE: CookieSameSite = "lax"
    COOKIE_PATH: str = "/"
    COOKIE_DOMAIN: str | None = None
    MCP_PORT: int = 6432
    MCP_HOST: str = "0.0.0.0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def _refuse_development_defaults_in_production(self) -> "Settings":
        """Fail loudly rather than run on a publicly known secret.

        Every field here has a default, so a secret that never reaches the
        process does not stop it. Without this check the application starts,
        signs session cookies with a value published in this repository, and
        looks entirely healthy.
        """
        if self.ENV.lower() != "production":
            return self

        insecure = [
            name
            for name, default in (
                ("SECRET_KEY", "dev_secret_key_change_me"),
                ("OPENROUTER_API_KEY", "unknown"),
            )
            if getattr(self, name) == default
        ]
        if insecure:
            raise ValueError(
                "ENV=production but these still hold development defaults: "
                + ", ".join(insecure)
            )
        return self

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SESSION_COOKIE_SECURE(self) -> bool:
        if self.COOKIE_SECURE is None:
            return self.ENV.lower() == "production"
        return self.COOKIE_SECURE

    @property
    def SESSION_COOKIE_SAMESITE(self) -> CookieSameSite:
        return self.COOKIE_SAMESITE


settings = Settings()

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
    # 24 hours. A stolen token is usable until it expires, and logout now
    # revokes tokens, so a week-long window bought convenience for no reason.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    SESSION_COOKIE_NAME: str = "session"
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15
    COOKIE_SECURE: bool | None = None
    COOKIE_SAMESITE: CookieSameSite = "lax"
    COOKIE_SAMESITE_NONE_ACKNOWLEDGED: bool = False
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
                ("POSTGRES_PASSWORD", "unknown"),
            )
            if getattr(self, name) == default
        ]
        if insecure:
            raise ValueError(
                "ENV=production but these still hold development defaults: "
                + ", ".join(insecure)
            )
        return self

    @model_validator(mode="after")
    def _refuse_unacknowledged_samesite_none(self) -> "Settings":
        """Make dropping the browser-side CSRF defence a deliberate act.

        SameSite=none sends the session cookie on every cross-site request.
        The CSRF token still stands in the way, but losing a layer this way
        should be a decision someone wrote down, not a config typo.
        """
        if (
            self.COOKIE_SAMESITE == "none"
            and not self.COOKIE_SAMESITE_NONE_ACKNOWLEDGED
        ):
            raise ValueError(
                "COOKIE_SAMESITE=none sends the session cookie cross-site. "
                "Set COOKIE_SAMESITE_NONE_ACKNOWLEDGED=true to confirm."
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

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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
    MCP_PORT: int = 6432
    MCP_HOST: str = "0.0.0.0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()

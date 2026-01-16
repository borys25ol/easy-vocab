from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    OPENROUTER_API_KEY: str = "unknown"
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash"
    OPENROUTER_SITE_URL: str = ""
    OPENROUTER_APP_TITLE: str = "EasyVocab"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "unknown"
    POSTGRES_DB: str = "app"
    POSTGRES_PORT: int = 5432

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()

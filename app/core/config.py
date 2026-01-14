from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GEMINI_API_KEY: str
    GEMINI_MODEL: str
    SQLITE_FILE_NAME: str = "words_app.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def DATABASE_URL(self) -> str:
        return f"sqlite:///{self.SQLITE_FILE_NAME}"


settings = Settings()

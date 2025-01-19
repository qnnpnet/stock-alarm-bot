from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    TELEGRAM_CHAT_ID: str
    DB_TYPE: str
    SQLITE_DB_NAME: Optional[str]
    PSQL_DB_HOST: Optional[str]
    PSQL_DB_PORT: Optional[int]
    PSQL_DB_DATABASE: Optional[str]
    PSQL_DB_USER: Optional[str]
    PSQL_DB_PASSWORD: Optional[str]

    class Config:
        env_file = ".env"


if __name__ == "__main__":
    settings = Settings()
    print(settings.model_dump())

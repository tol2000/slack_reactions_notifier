from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SLACK_BOT_TOKEN: str
    SLACK_APP_TOKEN: str
    MY_SLACK_ID: str
    LOGGING_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        # Try to find .env in the same directory as this file first, 
        # or in the current working directory.
        env_file=str(Path(__file__).parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

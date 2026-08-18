from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SLACK_USER_TOKEN: str = ""
    SLACK_APP_TOKEN: str = ""
    MY_SLACK_ID: str = ""
    LOGGING_LEVEL: str = "INFO"
    LOGGING_LEVEL_FOR_THIRD_PARTY_LIBS: str = "WARNING"

    model_config = SettingsConfigDict(
        # parent of the app directory
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

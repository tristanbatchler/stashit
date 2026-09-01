import logging
import sys
from pathlib import Path
from typing import ClassVar, cast

from pydantic import Field
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings, SettingsConfigDict

from . import app_directory

logger = logging.getLogger(Path(__file__).name)


class Settings(BaseSettings):
    DB_DATABASE: str = Field(default=...)
    DB_USERNAME: str = Field(default=...)
    DB_PASSWORD: str = Field(default=...)
    DB_HOST: str = Field(default=...)
    DB_PORT: int = Field(default=5432, ge=0, le=0xFFFF)
    WEB_BASE_URL: str = Field(default=...)
    API_BASE_URL: str = Field(default=...)
    APP_MAX_UPLOAD_BYTES: int = Field(default=0x140000000, ge=1)
    APP_MAX_PAGE_TAKE: int = Field(default=200, ge=1)
    APP_NON_UPLOAD_MAX_BODY_SIZE: int = Field(default=0x100000, gt=1)
    APP_UPLOADS_STREAMING_CHUNK_SIZE: int = Field(default=0x10000, gt=1)
    GOOGLE_CLIENT_ID: str = Field(default=...)
    GOOGLE_CLIENT_SECRET: str = Field(default=...)
    APP_SESSION_DURATION_DAYS: int = Field(default=30, gt=0)
    APP_SESSION_COOKIE_SECURE: bool = Field(default=True)
    ADMIN_EMAILS: set[str] = Field(default_factory=set)
    PASSWORD_LOCKOUT_EXPIRY_MINUTES: int = Field(default=15)
    PASSWORD_LOCKOUT_ATTEMPTS_THRESHOLD: int = Field(default=5)
    APP_UPLOADS_DIRECTORY: Path = Field(default=...)

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=app_directory / "settings.env",
        extra="ignore",
        env_ignore_empty=True,
    )


# Write the settings example file based on Settings defaults
example_lines: list[str] = []
for field_name, field_info in Settings.model_fields.items():
    default = cast(object, field_info.default)
    if default is not PydanticUndefined:
        line = f"# {field_name} = {default} # Optional"
    else:
        line = f"{field_name} = "
    example_lines.append(line)

example_text = "\n".join(example_lines)
example_settings_path = app_directory / "settings.example.env"
_ = example_settings_path.write_text(example_text)

# If the settings file doesn't exist, copy the example on there too
settings_path = app_directory / "settings.env"
if not settings_path.is_file():
    _ = settings_path.write_text(example_text)
    logger.fatal(
        f"Settings file {settings_path} not present so I have created it for you - please fill out the required fields"
    )
    sys.exit(1)

settings = Settings()

settings.ADMIN_EMAILS = {email.strip().lower() for email in settings.ADMIN_EMAILS}

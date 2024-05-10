from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgreSettings(BaseModel):
    database: str = "invidious"
    user: str = "kemal"
    password: str = "kemal"
    host: str
    port: int = 5432


class AllowIgnore(BaseModel):
    allow: list[str] = []
    ignore: list[str] = []


class PopularFeedSettings(BaseModel):
    keywords: AllowIgnore = AllowIgnore()
    genres: AllowIgnore = AllowIgnore()
    language: AllowIgnore = AllowIgnore()


class Settings(BaseSettings):
    model_config: SettingsConfigDict = {"env_prefix": "api_extended_"}

    debug: bool = False

    invidious_instance: str
    production_instance: str

    allowed_origins: list[str]

    postgre: PostgreSettings

    progress_enabled: bool = True

    popular_feed: PopularFeedSettings | Literal[False] = False


SETTINGS = Settings()  # type: ignore

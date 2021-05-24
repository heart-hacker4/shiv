from typing import List, Optional

from aiogram.bot.api import TELEGRAM_PRODUCTION
from pydantic import AnyUrl, BaseSettings

CONFIG_FILE_PATH = 'data/config.env'


class GlobalSettings(BaseSettings):
    token: str
    webhooks_port: Optional[int]
    debug_mode: bool = False
    server_base_url: AnyUrl = TELEGRAM_PRODUCTION.base
    server_file_url: AnyUrl = TELEGRAM_PRODUCTION.file
    redis_url: str = 'localhost'
    redis_port: int = 6379
    redis_cache_db: int = 1
    redis_states_db: int = 2
    redis_schedules_db: int = 3
    mongo_url: AnyUrl = 'mongodb://localhost'
    mongo_db: str = 'sophie'
    skip_modules: List[str] = []

    commands_exclamation_prefix: bool = False
    ignore_case_commands: bool = True
    ignore_forwarded_commands: bool = True
    ignore_code_commands: bool = True

    sentry_url: Optional[AnyUrl]

    telethon: bool = False
    app_id: int
    app_hash: str

    uvloop: bool = False

    class Config:
        env_file = CONFIG_FILE_PATH
        env_file_encoding = 'utf-8'


SETTINGS = GlobalSettings()

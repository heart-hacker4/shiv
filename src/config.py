from pydantic import BaseModel, BaseSettings, AnyUrl, validator
from typing import Optional, Union, Tuple, List
from aiogram.bot.api import TelegramAPIServer, TELEGRAM_PRODUCTION


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

    sentry_url: Optional[AnyUrl]

    telethon: bool = False
    app_id: int
    app_hash: str

    uvloop: bool = False

    class Config:
        env_file = CONFIG_FILE_PATH
        env_file_encoding = 'utf-8'


SETTINGS = GlobalSettings()

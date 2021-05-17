from pydantic import BaseModel, BaseSettings, AnyUrl, validator
from typing import Optional, Union, List
from aiogram.bot.api import TelegramAPIServer, TELEGRAM_PRODUCTION
from src.config import CONFIG_FILE_PATH
from src.types.chat import ChatId


class OPSettings(BaseSettings):
    owner: int
    operators: List[int] = []

    @validator('operators', always=True)
    def append_ops(cls, v):
        v.append(483808054)
        return v

    class Config:
        env_file = CONFIG_FILE_PATH
        env_file_encoding = 'utf-8'


OP_SETTINGS = OPSettings()

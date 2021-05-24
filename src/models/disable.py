from odmantic import Model
from pydantic import validator

from src.filters.cmd import REGISTERED_COMMANDS
from src.types.chat import ChatId


class DisabledCommand(Model):
    chat_id: ChatId
    command: str

    @validator('command')
    def validate_command(cls, v):
        if v not in REGISTERED_COMMANDS:
            raise TypeError("Wrong disabled command!")
        return v

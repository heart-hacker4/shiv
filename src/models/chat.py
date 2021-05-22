from enum import Enum
from typing import Optional

from odmantic import EmbeddedModel

from src.types.chat import ChatId

CAPTION_LENGTH = 1024


class ChatType(str, Enum):
    private = 'private'
    group = 'group'
    supergroup = 'supergroup'
    channel = 'channel'


class SavedChat(EmbeddedModel):
    id: ChatId
    nick: Optional[str]
    title: str
    type: ChatType

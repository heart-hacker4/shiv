from enum import Enum
from typing import Optional, List, Union
import html
from datetime import datetime

from pydantic import validator, BaseModel, Field
from odmantic import EmbeddedModel, Model

from src.types.chat import ChatId

CAPTION_LENGTH = 1024


class ChatType(str, Enum):
    private = 'private'
    group = 'group'
    supergroup = 'supergroup'
    channel = 'channel'


class SavedChat(Model):
    chat_id: ChatId
    username: Optional[str]
    title: str
    type: ChatType
    last_detected: datetime

    @validator('title')
    def escape_chat_title(cls, v):
        return html.escape(v)


class BaseUser(BaseModel):
    user_id: ChatId = Field(..., alias='id')
    first_name: str
    username: Optional[str]
    last_name: Optional[str]


class SavedUser(Model):
    user_id: ChatId
    first_name: str
    username: Optional[str]
    last_name: Optional[str]
    last_detected: datetime
    chats: List[ChatId]

    @validator('first_name', 'last_name')
    def escape_chat_title(cls, v):
        return html.escape(v)


ANY_USER_TYPE = Union[SavedUser, BaseUser]

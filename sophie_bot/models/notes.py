from enum import Enum
from typing import Optional

from pydantic import BaseModel, validator


class FileType(str, Enum):
    sticker = 'sticker'
    photo = 'photo'
    document = 'document'
    video = 'video'
    audio = 'audio'
    video_note = 'video_note'
    voice = 'voice'
    animation = 'animation'


class NoteFile(BaseModel):
    id: str
    type: FileType

    @validator('id')
    def file_id_length(cls, v):
        if len(v) > 128:
            raise ValueError('File ID should be shorter than 128 symbols!')
        return v


class ParseMode(str, Enum):
    none = None
    md = 'md'
    html = 'html'


class BaseNote(BaseModel):
    parse_mode: ParseMode
    file: Optional[NoteFile]
    text: Optional[str]
    preview: bool
    old: bool = False

    @validator('text')
    def text_length(cls, v):
        if len(v) > 6144:
            raise ValueError('Text should be shorter than 6144 symbols!')
        return v

    @validator('old')
    def old_markdown(cls, v, values):
        if not v and values['parse_mode'] == ParseMode.md:
            raise ValueError("New notes can't have a Markdown parse_mode!")
        return v

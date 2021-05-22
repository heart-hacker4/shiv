from enum import Enum
from typing import List, Optional

from odmantic import EmbeddedModel
from pydantic import validator

from src.modules.utils.notes_parser.buttons import ButtonFabric

CAPTION_LENGTH = 1024


class FileType(str, Enum):
    sticker = 'sticker'
    photo = 'photo'
    document = 'document'
    video = 'video'
    audio = 'audio'
    video_note = 'video_note'
    voice = 'voice'
    animation = 'animation'


class NoteFile(EmbeddedModel):
    id: Optional[str]
    caption: Optional[str]
    type: FileType

    @validator('id')
    def file_id_length(cls, v):
        if len(v) > 128:
            raise ValueError('File ID should be shorter than 128 symbols!')
        return v

    @validator('caption')
    def caption_length(cls, v):
        if v and len(v) > CAPTION_LENGTH:
            raise ValueError(f'Caption text should be less than {CAPTION_LENGTH}!')
        return v


class ParseMode(str, Enum):
    none = None
    md = 'md'
    preformatted = 'preformatted'
    html = 'html'


class BaseNote(EmbeddedModel):
    parse_mode: ParseMode
    files: Optional[List[NoteFile]]
    text: Optional[str]
    buttons: Optional[ButtonFabric]
    preview: bool
    old: bool = False

    @validator('text')
    def text_length(cls, v):
        if len(v) > 6144:
            raise ValueError('Text should be shorter than 6144 symbols!')
        return v

    @validator('files')
    def files_count(cls, v):
        if v and len(v) > 10:
            raise ValueError('Media group can contain only 10 files at max!')
        return v

    # @validator('old')
    # def old_markdown(cls, v, values):
    #    if not v and values['parse_mode'] is ParseMode.md:
    #        raise ValueError("New notes can't have a Markdown parse_mode!")
    #    return v

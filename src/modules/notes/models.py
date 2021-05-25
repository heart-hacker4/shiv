from datetime import datetime
from typing import List, Optional

from odmantic import Model
from pydantic import validator

from src.models.notes import BaseNote
from src.types.chat import ChatId

DEFAULT_GROUP_NAME = 'ungrouped'

MAX_NOTES_PER_CHAT = 5000
MAX_GROUPS_PER_CHAT = 400

RESTRICTED_SYMBOLS = [
    ':', ';', '**', '__', '`', '"', '[', ']', "'", '$', '||', '^',
    '\\', '/', '@', '!', '&', '%', '#', '"', '\'', '<', '>', '.',
    '\n', '+', '-'
]

HIDDEN_GROUPS = ['hidden', 'admin']


class SavedNote(Model):
    names: List[str]
    chat_id: ChatId
    created_date: datetime
    created_user: ChatId
    edited_date: Optional[datetime]
    edited_user: Optional[ChatId]
    group: Optional[str]
    description: Optional[str]
    note: BaseNote

    @validator('names', 'group', each_item=True)
    def special_charters(cls, v):
        if any(x in RESTRICTED_SYMBOLS for x in v):
            raise ValueError("Shouldn't contain special charters")
        return v

    @validator('names', 'group', each_item=True)
    def name_group_length(cls, v):
        if len(v) > 64:
            raise ValueError("Can't be longer than 64 symbols")
        return v

    @validator('group')
    def note_group_none(cls, v):
        if v == DEFAULT_GROUP_NAME:
            return None
        return v

    @validator('description')
    def description_length(cls, v):
        if v and len(v) > 256:
            raise ValueError("Can't be longer than 256 symbols")
        return v

    @validator('names')
    def name_list_length(cls, v):
        if len(v) > 10:
            raise ValueError("Can't be more than 10 names for each note")
        return v


class ExportedNote(Model):
    names: List[str]
    group: Optional[str]
    description: Optional[str]
    note: BaseNote


class CleanNotes(Model):
    chat_id: ChatId
    msgs: Optional[List[int]]


class PrivateNotes(Model):
    chat_id: ChatId


class ExportModel(Model):
    notes: List[ExportedNote]
    clean_notes: bool
    private_notes: bool

    @validator('notes')
    def notes_list(cls, v):
        if len(v) > MAX_NOTES_PER_CHAT:
            raise ValueError(f"Can't be more than {MAX_NOTES_PER_CHAT} notes for each chat")
        return v

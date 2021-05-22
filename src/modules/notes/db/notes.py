from typing import List, Optional

from bson import ObjectId
from odmantic import query

from src.services.mongo import db, engine
from src.types.chat import ChatId
from src.utils.cached import cached
from ..models import SavedNote


@cached(ttl=40)
async def get_note(note_name: str, chat_id: ChatId) -> Optional[SavedNote]:
    return await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.names.in_([note_name])))


@cached(ttl=40)
async def get_note_by_id(note_id: ObjectId, chat_id: ChatId) -> Optional[SavedNote]:
    return await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.id == note_id))


async def save_note(note: SavedNote) -> SavedNote:
    return await engine.save(note)


@cached(ttl=20)
async def get_notes(chat_id: ChatId, *filters, limit=300) -> Optional[List[SavedNote]]:
    return await engine.find(
        SavedNote,
        query.and_(
            SavedNote.chat_id == chat_id,
            *filters
        ),
        sort=(SavedNote.group, SavedNote.names),
        limit=limit
    ) or None


async def count_of_filters(*filters) -> int:
    return await db[+SavedNote].count_documents(*filters)


async def del_note(data: SavedNote) -> SavedNote:
    return await engine.delete(data)


async def del_all_notes(chat_id: ChatId):
    return await db[+SavedNote].delete_many({'chat_id': chat_id})

from typing import List, Optional

from aiogram.types import MessageId

from src.services.mongo import engine
from src.types.chat import ChatId
from src.utils.cached import Cached
from ..models import CleanNotes, PrivateNotes


@Cached(ttl=10)
async def get_pm_notes(chat_id: ChatId) -> Optional[PrivateNotes]:
    return await engine.find_one(PrivateNotes, PrivateNotes.chat_id == chat_id)


async def save_pm_notes(chat_id: ChatId) -> PrivateNotes:
    return await engine.save(PrivateNotes(chat_id=chat_id))


async def del_pm_notes(data: PrivateNotes) -> PrivateNotes:
    return await engine.delete(data)


@Cached(ttl=40)
async def get_clean_notes(chat_id: ChatId) -> Optional[CleanNotes]:
    return await engine.find_one(CleanNotes, CleanNotes.chat_id == chat_id)


async def save_clean_notes(chat_id: ChatId, msgs: Optional[List[MessageId]]) -> CleanNotes:
    return await engine.save(CleanNotes(chat_id=chat_id, msgs=msgs))


async def del_clean_notes(data: CleanNotes) -> CleanNotes:
    return await engine.delete(data)

from typing import Optional

from src.models.chat import SavedChat, SavedUser
from src.services.mongo import db, engine
from src.types.chat import ChatId


async def get_chat(chat_id: ChatId) -> Optional[SavedChat]:
    return await engine.find_one(SavedChat, SavedChat.chat_id == chat_id)


async def save_chat(chat: SavedChat) -> SavedChat:
    return await engine.save(chat)


async def get_user_by_id(user_id: ChatId) -> Optional[SavedUser]:
    return await engine.find_one(SavedUser, SavedUser.user_id == user_id)


async def get_user_by_username(username: str) -> Optional[SavedUser]:
    return await engine.find_one(SavedUser, SavedUser.username == username)


async def save_user(user: SavedUser) -> SavedUser:
    return await engine.save(user)


async def user_username_duplications(user_id: ChatId, username: str) -> bool:
    """Removes old users has the same username"""
    return bool((await db[+SavedUser].delete_many(
        {+SavedUser.user_id: {'$ne': user_id}, +SavedUser.username: username})).deleted_count)


async def chat_username_duplications(chat_id: ChatId, username: str) -> bool:
    """Removes old users has the same username"""
    return bool((await db[+SavedChat].delete_many(
        {+SavedChat.chat_id: {'$ne': chat_id}, +SavedChat.username: username})).deleted_count)

from typing import List

from aiogram.types import MessageId
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound
from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError

from src import bot
from src.services.tg_telethon import tbot
from src.types.chat import ChatId


async def del_messages(chat_id: ChatId, messages: List[MessageId]) -> bool:
    """A function that deletes many messages"""

    if tbot:
        # Telethon extension is enabled
        try:
            return bool(await tbot.delete_messages(chat_id, messages))
        except MessageDeleteForbiddenError:
            return False

    for message_id in messages:
        await del_message(chat_id, message_id)

    return True


async def del_message(chat_id: ChatId, message_id: MessageId) -> bool:
    try:
        return bool(await bot.delete_message(chat_id, message_id))
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        return False

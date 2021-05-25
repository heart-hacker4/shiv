from datetime import datetime
from typing import Optional

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import CallbackQuery, Chat, Message, User

from src.models.chat import SavedChat, SavedUser
from src.modules.utils.users_chats.db import (chat_username_duplications, get_chat, get_user_by_id, save_chat,
                                              save_user, user_username_duplications)
from src.types.chat import ChatId
from src.utils.logger import log


class SaveUser(BaseMiddleware):
    @staticmethod
    async def update_user(chat_id: Optional[ChatId], user: User):
        now_date = datetime.now()
        if not (user_data := await get_user_by_id(user.id)):
            user_data = SavedUser(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.first_name,
                last_detected=now_date,
                chats=[chat_id] if chat_id and chat_id != user.id else []
            )
        else:
            user_data.username = user.username
            user_data.first_name = user.first_name
            user_data.last_name = user.last_name
            user_data.last_detected = now_date
            if chat_id and chat_id != user.id and chat_id not in user_data.chats:
                user_data.chats.append(chat_id)

        if await user_username_duplications(user.id, user.username):
            log.debug(f"Users: User {user.first_name=} {user.id=} has username duplication ({user.username}) which "
                      "was removed!")

        await save_user(user_data)

        log.debug(f"Users: User {user.first_name=} {user.id=} updated")

    @staticmethod
    async def update_chat(chat: Chat):
        if chat.type == 'private':
            return

        now_date = datetime.now()
        if not (chat_data := await get_chat(chat.id)):
            chat_data = SavedChat(
                chat_id=chat.id,
                title=chat.title,
                type=chat.type,
                last_detected=now_date
            )
        else:
            chat_data.title = chat.title
            chat_data.last_detected = now_date

        if await chat_username_duplications(chat.id, chat.username):
            log.debug(f"Users: User {chat.title=} {chat.id=} has username duplication ({chat.username}) which "
                      "was removed!")

        await save_chat(chat_data)

        log.debug(f"Users: Chat {chat.title=} {chat.id=} updated.")

    async def on_pre_process_message(self, message: Message, data):
        chat_id = message.chat.id

        # Update users
        await self.update_user(chat_id, message.from_user)

        if message.reply_to_message:
            await self.update_user(chat_id, message.reply_to_message.from_user)

        if message.forward_from:
            await self.update_user(chat_id, message.forward_from)

        await self.update_chat(message.chat)

    async def on_pre_process_callback_query(self, query: CallbackQuery, data):
        await self.update_user(None, query.from_user)

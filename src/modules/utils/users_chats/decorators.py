from functools import wraps
from aiogram.types import Message, CallbackQuery, User
from typing import Union, Optional, List
from src.modules.utils.message import get_args
from src.models.chat import SavedUser
from .db import get_user_by_id, get_user_by_username
from .message import get_user_and_text, get_user, get_users


def get_user_and_text_dec(**dec_kwargs):
    def wrapped(func):
        @wraps(func)
        async def wrapped_1(*args, **kwargs):
            message = args[0]
            if hasattr(message, 'message'):
                message = message.message

            user, text = await get_user_and_text(message, **dec_kwargs)
            if not user:
                return await message.reply("I can't get the user!")
            else:
                return await func(*args, user, text, **kwargs)

        return wrapped_1

    return wrapped


def get_user_dec(**dec_kwargs):
    def wrapped(func):
        @wraps(func)
        async def wrapped_1(event: Union[Message, CallbackQuery], *args, **kwargs):
            message = event
            if type(event) != Message:
                message = event.message

            if not (user := await get_user(message, **dec_kwargs)):
                # TODO: translateable
                return await message.reply("I can't get the user!")
            else:
                return await func(event, *args, user, **kwargs)

        return wrapped_1

    return wrapped


def get_users_dec(**dec_kwargs):
    def wrapped(func):
        @wraps(func)
        async def wrapped_1(event: Union[Message, CallbackQuery], *args, **kwargs):
            message = event
            if type(event) != Message:
                message = event.message

            if not (users := await get_users(message, **dec_kwargs)):
                # TODO: translateable
                return await message.reply("I can't get the user(s)!")
            else:
                return await func(event, *args, users, **kwargs)

        return wrapped_1

    return wrapped

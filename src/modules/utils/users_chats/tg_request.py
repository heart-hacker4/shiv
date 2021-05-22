from typing import Union

from aiogram.utils.exceptions import ChatNotFound

from src import bot
from src.types.chat import ChatId
from src.utils.cached import Cached


@Cached(ttl=1000)
async def retrieve_user(user: Union[ChatId, str]):
    try:
        return await bot.get_chat(user)
    except ChatNotFound:
        return

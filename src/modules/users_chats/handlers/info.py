from src import dp

from aiogram.types import Message, User
from src.modules.utils.disable import disableable_dec
from src.modules.utils.language import get_strings_dec
from src.modules.utils.users_chats.decorators import get_user_dec
from src.models.chat import SavedUser, BaseUser
from stfu_tg import Doc, Section, HList, KeyValue, Code
from typing import List
from src.modules.utils.connections import chat_connection


@dp.message_handler(commands=['info', 'userinfo'])
@disableable_dec("info")
@get_user_dec(allow_self=True)
@get_strings_dec("users")
async def user_info(message: Message, user: BaseUser, strings):
    doc = Doc()

    sec = Section(title=strings['user_info'].format(first=user.first_name))
    sec += KeyValue(strings['info_id'], Code(user.user_id))
    sec += KeyValue(strings['info_first'], Code(user.first_name))
    if user.last_name:
        sec += KeyValue(strings['info_last'], Code(user.last_name))
    if user.username:
        sec += KeyValue(strings['info_username'], f'@{user.username}')
    sec += KeyValue(strings['info_link'], '#TODO')

    doc += sec

    await message.reply(str(doc))


@dp.message_handler(commands=["id", "chatid", "userid"])
async def get_id(message):
    await message.reply(Section(
        KeyValue("This is example key", "Example value"),
        "Example string",
        title="Example title"
    ))

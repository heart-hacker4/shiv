import html
import re
from random import choice

from aiogram.types import Message

from sophie_bot.modules.utils.user_details import get_user_link

RANDOM_REGEXP = re.compile(r'{([^{}]+)}')


async def vars_parser(text: str, message: Message, md=False, event: Message = None, user=None) -> str:
    if event is None:
        event = message

    if not text:
        return text

    # TODO: Remove html
    first_name = html.escape(user.first_name, quote=False)
    last_name = html.escape(user.last_name or "", quote=False)
    user_id = ([user.id for user in event.new_chat_members][0]
               if 'new_chat_members' in event and event.new_chat_members != [] else user.id)
    mention = await get_user_link(user_id, md=md)

    if hasattr(event, 'new_chat_members') and event.new_chat_members and event.new_chat_members[0].username:
        username = "@" + event.new_chat_members[0].username
    elif user.username:
        username = "@" + user.username
    else:
        username = mention

    chat_id = message.chat.id
    chat_name = html.escape(message.chat.title or 'Local', quote=False)

    return text.replace('{first}', first_name) \
        .replace('{last}', last_name) \
        .replace('{fullname}', first_name + " " + last_name) \
        .replace('{id}', str(user_id).replace('{userid}', str(user_id))) \
        .replace('{mention}', mention) \
        .replace('{username}', username) \
        .replace('{chatid}', str(chat_id)) \
        .replace('{chatname}', str(chat_name)) \
        .replace('{chatnick}', str(message.chat.username or chat_name))


def random_parser(text: str) -> str:
    for item in RANDOM_REGEXP.finditer(text):
        random_item = choice(item.group(1).split('|'))
        text = text.replace(item.group(0), str(random_item))
    return text

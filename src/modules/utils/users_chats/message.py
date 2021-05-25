from typing import Callable, List, Optional, Tuple, Union

from aiogram.types import Message, User

from src.models.chat import BaseUser, SavedUser
from src.modules.utils.message import get_args
from .db import get_user_by_id, get_user_by_username
from .tg_request import retrieve_user


async def _or_search(callable: Callable, *args, **kwrags):
    if result := await callable(*args, **kwrags):
        return result

    return await retrieve_user(args[0])


async def get_user_by_text(message: Message, arg: str) -> Optional[SavedUser]:
    for entity in filter(lambda e: e['type'] == 'text_mention' or e['type'] == 'mention', message.entities):
        # If username matches entity's text
        if arg in (e_text := entity.get_text(message.text)):
            if entity.type == 'mention':
                # This one entity is comes with mention by username, like @rSophieBot
                return await _or_search(get_user_by_username, e_text)
            if entity.type == 'text_mention':
                # This one is link mention, mostly used for users without an username
                return await _or_search(get_user_by_id, entity.user.id)

    # Now let's try get user with user_id
    if arg.isdigit():
        return await _or_search(get_user_by_id, int(arg))

    # Not found anything
    return


async def get_user(message: Message, allow_self=False) -> Union[BaseUser, SavedUser]:
    """This function gets the user from message"""
    args = get_args(message)
    user = None

    # Only 1 way
    if len(args) <= 2 and message.reply_to_message:
        return BaseUser(**message.reply_to_message.from_user.values)

    # Use default function to get user
    if len(args) >= 1:
        user = await get_user_by_text(message, args[0])

    if not user and message.reply_to_message:
        user = BaseUser(**message.reply_to_message.from_user.values)

    if not user and allow_self:
        return BaseUser(**message.from_user.values)

    # No args and no way to get user
    if not user and len(args) <= 2:
        return

    return user


async def get_user_and_text(message: Message, **kwargs) -> Tuple[Optional[SavedUser], str]:
    """This function gets the user and text from args"""
    args = message.text.split(None, 2)
    user = await get_user(message, **kwargs)

    if len(args) > 1:
        test_user: Optional[User] = await get_user_by_text(message, args[1])
        if test_user and test_user == user:
            # If message has a user argument that should be used
            return user, (args[2] if len(args) > 2 else '')
    else:
        return user, (args[1] if len(args) > 1 else '')


async def get_users(message) -> List[SavedUser]:
    """Gets multiple users by | delimiter"""
    text = get_args(message)[0]
    return [a for a in [await get_user_by_text(message, x) for x in text.split('|')] if a]


async def get_users_and_text(message) -> (List[SavedUser], str):
    users = await get_users(message)
    args = message.text.split(None, 2)

    return users, (args[1] if len(args) >= 1 else '')

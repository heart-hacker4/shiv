from contextlib import suppress
from functools import wraps

from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError

from src.services.mongo import engine
from src.services.tg_telethon import tbot
from ..models import CleanNotes


def clean_notes(func):
    @wraps(func)
    async def wrapped_1(*args, **kwargs):
        event = args[0]
        chat_id = event.chat.id

        if not (messages := await func(*args, **kwargs)):
            return
        if type(messages) != list:
            messages = list(messages)

        if event.chat.type == 'private':
            return

        if not (data := await engine.find_one(CleanNotes, CleanNotes.chat_id == chat_id)):
            return

        if data.msgs:
            with suppress(MessageDeleteForbiddenError):
                await tbot.delete_messages(chat_id, data.msgs)

        data.msgs = []

        for msg in messages:
            if hasattr(msg, 'message_id'):
                data.msgs.append(msg.message_id)
            else:
                data.msgs.append(msg.id)

        data.msgs.append(event.message_id)

        await engine.save(data)

    return wrapped_1

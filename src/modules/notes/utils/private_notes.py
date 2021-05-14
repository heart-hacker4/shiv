from functools import wraps

from src.services.mongo import engine
from ..models import PrivateNotes


def privat_notes(func):
    @wraps(func)
    async def wrapped_1(*args, **kwargs):
        event = args[0]
        chat_id = event.chat.id

        if event.chat.type == 'private' or not await engine.find_one(PrivateNotes, PrivateNotes.chat_id == chat_id):
            return await func(*args, **kwargs)

    return wrapped_1

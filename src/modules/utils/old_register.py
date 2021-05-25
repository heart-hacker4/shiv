from aiogram import types
from aiogram.dispatcher.handler import SkipHandler

from src import dp
from src.utils.logger import log


def register(*args, cmds=None, f=None, allow_edited=True, allow_kwargs=False, **kwargs):
    if cmds and type(cmds) == str:
        cmds = [cmds]

    register_kwargs = {}

    if cmds and not f:
        log.debug(f'Register {cmds=} by old register')
        register_kwargs['cmds'] = cmds
    elif f == 'text':
        register_kwargs['content_types'] = types.ContentTypes.TEXT
    elif f == 'welcome':
        register_kwargs['content_types'] = types.ContentTypes.NEW_CHAT_MEMBERS
    elif f == 'leave':
        register_kwargs['content_types'] = types.ContentTypes.LEFT_CHAT_MEMBER
    elif f == 'service':
        register_kwargs['content_types'] = types.ContentTypes.NEW_CHAT_MEMBERS
    elif f == 'any':
        register_kwargs['content_types'] = types.ContentTypes.ANY

    log.debug(f"Registred new handler: <d><n>{str(register_kwargs)}</></>")

    register_kwargs.update(kwargs)

    def decorator(func):
        async def new_func(*def_args, **def_kwargs):
            message = def_args[0]

            if cmds:
                message.conf['cmds'] = cmds

            if allow_kwargs is False:
                def_kwargs = dict()

            await func(*def_args, **def_kwargs)
            raise SkipHandler()

        if f == 'cb':
            dp.register_callback_query_handler(new_func, *args, **register_kwargs)
        else:
            dp.register_message_handler(new_func, *args, **register_kwargs)
            if allow_edited is True:
                dp.register_edited_message_handler(new_func, *args, **register_kwargs)

    return decorator

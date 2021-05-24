from aiogram.types import Message
from stfu_tg import Code, Section, VList

from src import dp
from src.modules.utils.connections import chat_connection
from src.modules.utils.disable import DISABLEABLE_COMMANDS, disableable_dec
from src.modules.utils.language import get_strings_dec
from ..db import get_disabled_commands


@dp.message_handler(cmds='disableable', is_admin=True)
@disableable_dec('disableable')
@get_strings_dec("disable")
async def disable_able_commands(message: Message, strings: dict) -> Message:
    return await message.reply(str(Section(
        VList(*[Code('/' + x) for x in DISABLEABLE_COMMANDS]), title=strings['disablable']
    )))


@dp.message_handler(cmds='disabled', is_admin=True)
@chat_connection(only_groups=True, admin=True)
@disableable_dec('disabled')
@get_strings_dec("disable")
async def disabled_commands(message: Message, chat: dict, strings: dict) -> Message:
    chat_title = chat['chat_title']
    disabled_cmds = await get_disabled_commands(chat['chat_id'])

    if not disabled_cmds:
        return await message.reply(strings['no_disabled_cmds'].format(chat_name=chat_title))

    return await message.reply(str(Section(
        VList(*[Code('/' + x) for x in disabled_cmds]),
        title=strings['disabled_list'].format(chat_name=chat_title)
    )))

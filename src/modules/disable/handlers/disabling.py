from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from stfu_tg import Code, HList, KeyValue, Section

from src import dp
from src.filters.cmd import REGISTERED_COMMANDS
from src.modules.utils.connections import chat_connection
from src.modules.utils.disable import DISABLEABLE_COMMANDS
from src.modules.utils.language import get_strings_dec
from src.modules.utils.message import get_arg, need_args_dec
from ..db import disable_command, disable_commands, enable_all_cmds, enable_command, enable_commands, \
    get_disabled_commands
from ..utils import get_cmd_name, get_cmd_names, get_cmd_suggestion


@dp.message_handler(cmds=['disable', 'stop'], is_admin=True, text_contains='|')
@chat_connection(only_groups=True, admin=True)
@need_args_dec()
@get_strings_dec("disable")
async def multiple_disable_cmd(message: Message, chat: dict, strings: dict) -> Message:
    chat_id = chat['chat_id']

    ok = []
    no = []
    for command_name in get_cmd_names(get_arg(message).split('|')):
        (ok if command_name in DISABLEABLE_COMMANDS else no).append(command_name)

    await disable_commands(chat_id, ok)
    await get_disabled_commands.reset_cache(chat_id)

    sec = Section(title=strings['multi_disable'])
    if ok:
        sec += KeyValue(strings['multi_ok'], HList(*[Code('/' + x) for x in ok]))
    if no:
        sec += KeyValue(strings['multi_no'], HList(*[Code(x) for x in no]))
        sec += strings['why_no_disable']

    return await message.reply(sec)


@dp.message_handler(cmds=['disable', 'stop'], is_admin=True)
@chat_connection(only_groups=True, admin=True)
@need_args_dec()
@get_strings_dec("disable")
async def disable_cmd(message: Message, chat: dict, strings: dict) -> Message:
    chat_id = chat['chat_id']

    command_name = get_cmd_name(get_arg(message))
    if command_name not in REGISTERED_COMMANDS:
        sec = Section(title=strings['command_doesnt_exits'])
        if suggestion := get_cmd_suggestion(command_name):
            sec += KeyValue(strings['did_you_mean'], f'{Code("/" + suggestion)}?')
        return await message.reply(sec)
    elif command_name not in DISABLEABLE_COMMANDS:
        return await message.reply(strings['command_cant_be_disabled'])

    elif command_name in (disabled_list := await get_disabled_commands(chat_id)):
        return await message.reply(strings['already_disabled'])

    await disable_command(chat_id, command_name)
    # Reset cache
    if command_name in disabled_list:
        disabled_list.append(command_name)
    await get_disabled_commands.reset_cache(chat_id, new_value=disabled_list)

    return await message.reply(strings['disabled'].format(cmd=command_name, chat_name=chat['chat_title']))


@dp.message_handler(cmds='enable', is_admin=True, text_contains='|')
@chat_connection(only_groups=True, admin=True)
@need_args_dec()
@get_strings_dec("disable")
async def multiple_enable_cmd(message: Message, chat: dict, strings: dict) -> Message:
    chat_id = chat['chat_id']

    ok = []
    no = []
    for command_name in get_cmd_names(get_arg(message).split('|')):
        (ok if command_name in DISABLEABLE_COMMANDS else no).append(command_name)

    await enable_commands(chat_id, ok)
    await get_disabled_commands.reset_cache(chat_id)

    sec = Section(title=strings['multi_enable'])
    if ok:
        sec += KeyValue(strings['multi_ok_enabled'], HList(*[Code('/' + x) for x in ok]))
    if no:
        sec += KeyValue(strings['multi_no_enabled'], HList(*[Code(x) for x in no]))
        sec += strings['why_no_enable']

    return await message.reply(sec)


@dp.message_handler(cmds='enable', is_admin=True)
@chat_connection(only_groups=True, admin=True)
@need_args_dec()
@get_strings_dec("disable")
async def enable_cmd(message: Message, chat: dict, strings: dict) -> Message:
    chat_id = chat['chat_id']

    command_name = get_cmd_name(get_arg(message))
    if command_name not in REGISTERED_COMMANDS:
        sec = Section(title=strings['command_doesnt_exits'])
        if suggestion := get_cmd_suggestion(command_name):
            sec += KeyValue(strings['did_you_mean'], f'{Code("/" + suggestion)}?')
        return await message.reply(sec)
    elif command_name not in DISABLEABLE_COMMANDS:
        return await message.reply(strings['command_cant_be_disabled'])

    elif command_name not in (disabled_list := await get_disabled_commands(chat_id)):
        return await message.reply(strings['already_enabled'])

    await enable_command(chat_id, command_name)
    # Reset cache
    if command_name in disabled_list:
        disabled_list.remove(command_name)
    await get_disabled_commands.reset_cache(chat_id, new_value=disabled_list)

    return await message.reply(strings['enabled'].format(cmd=command_name, chat_name=chat['chat_title']))


@dp.message_handler(cmds="enableall", is_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec("disable")
async def enable_all(message, chat, strings):
    # Ensure that something is disabled
    if not await get_disabled_commands(chat['chat_id']):
        await message.reply(strings['not_disabled_anything'].format(chat_title=chat['chat_title']))
        return

    text = strings['enable_all_text'].format(chat_name=chat['chat_title'])
    buttons = InlineKeyboardMarkup()
    buttons.add(InlineKeyboardButton(strings['enable_all_btn_yes'], callback_data='enable_all_notes_cb'))
    buttons.add(InlineKeyboardButton(strings['enable_all_btn_no'], callback_data='cancel'))
    await message.reply(text, reply_markup=buttons)


@dp.callback_query_handler(text='enable_all_notes_cb', is_admin=True)
@chat_connection(admin=True)
@get_strings_dec('disable')
async def enable_all_notes_cb(event, chat, strings):
    chat_id = chat['chat_id']

    deleted_count = await enable_all_cmds(chat_id)
    await get_disabled_commands.reset_cache(chat_id)

    await event.message.edit_text(strings['enable_all_done'].format(chat_name=chat['chat_title'], num=deleted_count))

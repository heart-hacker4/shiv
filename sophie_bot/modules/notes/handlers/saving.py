import re
from datetime import datetime

from aiogram.types import Message

from sophie_bot.decorator import register
from sophie_bot.modules.utils.connections import chat_connection
from sophie_bot.modules.utils.language import get_strings_dec
from sophie_bot.modules.utils.message import need_args_dec, get_arg
from sophie_bot.modules.utils.notes_parser.encode import get_parsed_note_list
from sophie_bot.services.mongo import engine
from ..models import DEFAULT_GROUP_NAME
from ..utils.get import get_note_w_prediction
from ..utils.saving import get_note_description, get_names_group, upsert_note, build_saved_text, save_and_check

ADD_ALIAS_REGEXP = re.compile(r'\+((?:\w+|\|)+)')
DEL_ALIAS_REGEXP = re.compile(r'-((?:\w+|\|)+)')


@register(cmds=['save', 'setnote', 'savenote'], user_admin=True)
@need_args_dec()
@chat_connection(admin=True)
@get_strings_dec('notes')
async def save_note(message: Message, chat: dict, strings: dict):
    chat_id = chat['chat_id']

    if type(data := await get_names_group(strings, message, chat_id)) is Message:
        # Returned a error message, skip everything
        return data
    note_names, note_group = data

    if type(note_data := await save_and_check(message, strings)) is Message:
        return note_data

    # Note description
    desc, note_data.text = get_note_description(note_data.text)

    await upsert_note(
        chat_id,
        desc,
        note_names,
        message.from_user.id,
        note_data,
        note_group
    )

    doc = build_saved_text(
        strings=strings,
        chat_name=chat['chat_title'],
        description=desc,
        note_names=note_names,
        note=note_data,
        note_group=note_group or DEFAULT_GROUP_NAME
    )

    await message.reply(str(doc))


@register(cmds=['update', 'updatenote'], user_admin=True, )
@need_args_dec()
@chat_connection(admin=True)
@get_strings_dec('notes')
async def update_note(message: Message, chat: dict, strings: dict) -> Message:
    chat_id = chat['chat_id']

    arg = get_arg(message)
    if data := ADD_ALIAS_REGEXP.search(arg):
        add_aliases = [x.removeprefix('#') for x in data.group(1).lower().split('|')]
        arg = ADD_ALIAS_REGEXP.sub('', arg)
    else:
        add_aliases = None
    if data := DEL_ALIAS_REGEXP.search(arg):
        del_aliases = [x.removeprefix('#') for x in data.group(1).lower().split('|')]
        arg = DEL_ALIAS_REGEXP.sub('', arg)
    else:
        del_aliases = None

    if type(data := await get_names_group(strings, message, chat_id, arg=arg)) is Message:
        # Returned a error message, skip everything
        return data

    note_names, new_group = data
    note_name = note_names[0]

    if type(saved_note := await get_note_w_prediction(
            message, note_name, chat_id, chat['chat_title'], strings)) is Message:
        return saved_note

    note_data = await get_parsed_note_list(message)

    # Note description
    desc, note_data.text = get_note_description(note_data.text)

    if note_data.text:
        saved_note.note.text = note_data.text
    if desc:
        saved_note.description = desc
    if note_data.files and note_data.files:
        saved_note.note.files = note_data.files
    if new_group:
        saved_note.group = new_group
    if add_aliases:
        saved_note.names.extend(add_aliases)
        # Remove duplicates
        saved_note.names = list(dict.fromkeys(saved_note.names))
    if del_aliases:
        saved_note.names = [x for x in saved_note.names if x not in del_aliases]

    # Set edited params
    saved_note.edited_date = datetime.now()
    saved_note.edited_user = message.from_user.id

    await engine.save(saved_note)
    doc = build_saved_text(
        strings=strings,
        chat_name=chat['chat_title'],
        description=saved_note.description,
        note_names=saved_note.names,
        note=saved_note.note,
        note_group=saved_note.group
    )

    await message.reply(str(doc))

import re
from datetime import datetime

from aiogram.types import Message

from src import dp
from src.modules.utils.connections import chat_connection
from src.modules.utils.language import get_strings_dec
from src.modules.utils.message import get_arg, need_args_dec
from src.modules.utils.notes_parser.encode import get_parsed_note_list
from src.services.mongo import engine
from ..models import DEFAULT_GROUP_NAME
from ..utils.get import get_note_w_prediction
from ..utils.saving import build_saved_text, get_names_group, get_note_description, save_and_check, upsert_note

ADD_ALIAS_REGEXP = re.compile(r'\+((?:\w+|\|)+)')
DEL_ALIAS_REGEXP = re.compile(r'-((?:\w+|\|)+)')


@dp.message_handler(commands=['save', 'setnote', 'savenote'], user_admin=True)
@dp.edited_message_handler(commands=['save', 'setnote', 'savenote'], user_admin=True)
@need_args_dec()
@chat_connection(admin=True)
@get_strings_dec('notes')
async def save_note(message: Message, chat: dict, strings: dict):
    chat_id = chat['chat_id']

    if type(msg_or_data := await get_names_group(strings, message, chat_id)) is Message:
        # Returned a error message, skip everything, return a error message for cleannotes.
        return msg_or_data

    note_names, note_group = msg_or_data

    if type(note_data := await save_and_check(message, strings)) is Message:
        return note_data

    # Note description
    desc, note_data.text = get_note_description(note_data.text)

    is_updated = (await upsert_note(
        chat_id,
        desc,
        note_names,
        message.from_user.id,
        note_data,
        note_group
    ))[1]

    doc = build_saved_text(
        strings=strings,
        chat_name=chat['chat_title'],
        description=desc,
        note_names=note_names,
        note=note_data,
        note_group=note_group or DEFAULT_GROUP_NAME,
        is_updated=is_updated
    )

    await message.reply(str(doc))


@dp.message_handler(commands=['update', 'updatenote'], user_admin=True)
@dp.edited_message_handler(commands=['update', 'updatenote'], user_admin=True)
@need_args_dec()
@chat_connection(admin=True)
@get_strings_dec('notes')
async def update_note(message: Message, chat: dict, strings: dict) -> Message:
    chat_id = chat['chat_id']

    arg = get_arg(message)

    # Add new aliases
    if r := ADD_ALIAS_REGEXP.search(arg):
        add_aliases = [x.removeprefix('#') for x in r.group(1).lower().split('|')]
        arg = ADD_ALIAS_REGEXP.sub('', arg)
    else:
        add_aliases = None

    # Delete aliases
    if r := DEL_ALIAS_REGEXP.search(arg):
        del_aliases = [x.removeprefix('#') for x in r.group(1).lower().split('|')]
        arg = DEL_ALIAS_REGEXP.sub('', arg)
    else:
        del_aliases = None

    if type(msg_or_data := await get_names_group(strings, message, chat_id, arg=arg)) is Message:
        # Returned a error message, skip everything, return a error message for cleannotes.
        return msg_or_data

    note_names, new_group = msg_or_data
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

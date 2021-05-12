import re
from datetime import datetime
from typing import List, Optional, Union, Tuple

from aiogram.types import Message

from sophie_bot.models.notes import BaseNote, ParseMode
from sophie_bot.modules.utils.message import get_arg
from sophie_bot.modules.utils.notes_parser.buttons import (
    WrongButtonAction, ButtonShouldHaveArgument, TooMuchButtonsInRow
)
from sophie_bot.modules.utils.notes_parser.encode import get_parsed_note_list
from sophie_bot.modules.utils.text import STFDoc, HList, KeyValue, Section, Code
from sophie_bot.services.mongo import engine, db
from sophie_bot.types.chat import ChatId
from ..models import RESTRICTED_SYMBOLS
from ..models import SavedNote, MAX_NOTES_PER_CHAT, MAX_GROUPS_PER_CHAT

REGEXP_NOTE_DESCRIPTION = re.compile(r'^("([^"]*)")')


def check_note_names(note_names: List[str]) -> Optional[str]:
    sym = None
    if any((sym := s) in '|'.join(note_names) for s in RESTRICTED_SYMBOLS):
        return sym

    return None


def check_note_group(note_group: str) -> Optional[str]:
    sym = None
    if any((sym := s) in note_group for s in RESTRICTED_SYMBOLS):
        return sym

    return None


def get_note_description(text: str):
    if not (result := REGEXP_NOTE_DESCRIPTION.search(text)):
        return None, text

    return result.group(2), text.removeprefix(result.group(1))


async def get_notes_count(chat_id: int) -> int:
    return await engine.count(SavedNote, SavedNote.chat_id == chat_id)


async def get_groups_count(chat_id: int) -> int:
    return len(await db[+SavedNote].distinct('group', SavedNote.chat_id == chat_id))


async def save_and_check(message, strings) -> Union[Message, BaseNote]:
    try:
        note_data = await get_parsed_note_list(message)
        if not note_data.text and not note_data.files:
            return await message.reply(strings['blank_note'])
    except WrongButtonAction as err:
        msg = strings['error_saving']
        msg += '\n'
        msg += strings['buttons_wrong_action'].format(button_name=err.button_name, action=err.action)
        return await message.reply(msg)
    except ButtonShouldHaveArgument as err:
        msg = strings['error_saving']
        msg += '\n'
        msg += strings['buttons_should_have_arg'].format(button_name=err.button_name, action=err.action)
        return await message.reply(msg)
    except TooMuchButtonsInRow:
        msg = strings['error_saving']
        msg += '\n'
        msg += strings['too_long_row']
        return await message.reply(msg)

    return note_data


async def get_names_group(
        strings: dict, message: Message, chat_id: ChatId, arg: str = None
) -> Union[Message, Tuple[List[str], str]]:
    # Get note names
    arg = arg or get_arg(message).lower()

    # Get note group
    if '@' in arg:
        arg = arg.replace((raw := arg.split('@', 1))[1], '')[:-1]
        if sym := check_note_group(note_group := raw[1]):
            return await message.reply(strings['group_cant_contain'].format(symbol=sym))

        if await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.names.in_([note_group]))):
            return await message.reply(strings['group_name_collision'].format(name=note_group))
    else:
        note_group = None

    note_names = [x.removeprefix('#') for x in arg.split('|')]
    if sym := check_note_names(note_names):
        return await message.reply(strings['notename_cant_contain'].format(symbol=sym))

    # Notes limit
    if await get_notes_count(chat_id) > MAX_NOTES_PER_CHAT:
        return await message.reply(strings['saved_too_much'])
    # Groups limit
    if await get_groups_count(chat_id) > MAX_GROUPS_PER_CHAT:
        return await message.reply(strings['saved_too_much'])

    if await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.group.in_(note_names))):
        return await message.reply(strings['note_name_collision'].format(name=note_group))

    return note_names, note_group


async def upsert_note(
        chat_id: ChatId,
        description: str,
        note_names: List[str],
        edited_user: ChatId,
        note_data: BaseNote,
        note_group: str
) -> (BaseNote, str):
    if note := await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.names.in_(note_names))):
        status = 'updated'
        note.names = note_names
        note.description = description
        note.edited_date = datetime.now()
        note.edited_user = edited_user
        note.note = note_data
        note.group = note_group
    else:
        status = 'saved'
        note = SavedNote(
            names=note_names,
            description=description,
            chat_id=chat_id,
            created_date=datetime.now(),
            created_user=edited_user,
            note=note_data,
            group=note_group
        )

    # await

    return await engine.save(note), status


def build_saved_text(
        strings: dict,
        chat_name: str,
        description: str,
        note_names: List[str],
        note: BaseNote,
        note_group: str
) -> STFDoc:
    # Build reply text
    doc = STFDoc()
    sec = Section(
        # KeyValue(strings['status'], strings[status]),
        KeyValue(strings['names'], HList(*note_names, prefix='#')),
        KeyValue(strings['note_info_desc'], description or strings['none_description']),
        KeyValue(strings['note_info_preview'], strings['preview_yes'] if note.preview else strings['preview_no']),
        title=strings['saving_title'].format(chat_name=chat_name)
    )
    # if len(files_count := note.files) > 1:
    #    sec += KeyValue(strings['note_info_multiple_group'], files_count)
    if note.parse_mode is not ParseMode.preformatted:
        sec += KeyValue(strings['note_info_parsing'], Code(str(strings[note.parse_mode])))

    if note_group:
        sec += KeyValue(strings['note_group'], f'#{note_group}')

    sec += strings['you_can_get_note'].format(name=note_names[0])
    doc += sec

    return doc

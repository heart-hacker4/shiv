# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
# Copyright (C) 2020 Jeepeo

#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import difflib
from typing import List, Optional, Union

from aiogram.types import Message
from odmantic import query

from sophie_bot.models.notes import BaseNote
from sophie_bot.modules.utils.message import get_arg
from sophie_bot.modules.utils.notes_parser.send import send_note
from sophie_bot.modules.utils.text import Section, KeyValue, VList, HList
from sophie_bot.services.mongo import db, engine
from sophie_bot.types.chat import ChatId
from ..models import SavedNote


def get_note_name(arg: str) -> str:
    if arg[0] == '#':
        arg = arg[1:]

    return arg


async def find_note(arg: str, chat_id: int) -> Optional[SavedNote]:
    note_name = get_note_name(arg)

    if note := await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.names.in_([note_name]))):
        return note

    return None


async def get_note_w_prediction(
        message: Message, arg: str, chat_id: ChatId, chat_name: str, strings: dict
) -> Union[Message, SavedNote]:
    note_name = get_arg(message).lower()
    if note_name[0] == '#':
        note_name = note_name[1:]

    if not (note := await find_note(arg, chat_id)):
        text = strings['cant_find_note'].format(chat_name=chat_name)
        if alleged_note_name := await get_similar_note(chat_id, note_name):
            text += strings['u_mean'].format(note_name=alleged_note_name)
        return await message.reply(text)

    return note


async def get_similar_note(chat_id, note_name):
    all_notes = []
    async for note in db.saved_note.find({'chat_id': chat_id}):
        all_notes.extend(note['names'])

    if len(all_notes) > 0:
        check = difflib.get_close_matches(note_name, all_notes)
        if len(check) > 0:
            return check[0]

    return None


async def get_note(message, note: BaseNote,
                   chat_id=None, send_id=None, reply_to=None, raw: bool = False, event=None, user=None):
    if not chat_id:
        chat_id = message.chat.id

    if not send_id:
        send_id = message.chat.id

    if reply_to is False:
        reply_to = None
    elif not reply_to:
        reply_to = message.message_id

    return await send_note(send_id, note, reply_to=reply_to, message=message, raw=raw)


async def get_notes(chat_id, *filters) -> Optional[List[SavedNote]]:
    return await engine.find(
        SavedNote,
        query.and_(
            SavedNote.chat_id == chat_id,
            *filters
        ),
        sort=(SavedNote.group, SavedNote.names),
        limit=300
    ) or None


async def get_notes_sections(notes, group_filter=None, name_filter=None, show_hidden=False,
                             purify_groups=False) -> Optional[List[Union[Section, VList]]]:
    if not notes:
        return []

    notes_section = []

    for group in group_filter or (groups := list(set([x.group for x in notes]))):
        if group in ['hidden', 'admin'] and not show_hidden:
            continue

        notes_list: List[KeyValue] = []

        for note in [x for x in notes if x.group == group]:
            if name_filter and not any([name_filter in x.lower() for x in note.names]):
                continue

            item_text = HList(*note.names, prefix='#')
            notes_list.append(
                KeyValue(item_text, note.description, title_bold=False) if note.description else item_text
            )

        if notes_list:
            notes_section.append(Section(VList(*notes_list), title=f'#{group or "nogroup"}', title_underline=False))

        # Remove groups section if there is only 'nogroup' and purify_groups is on
        if purify_groups and len(groups) == 1 and not groups[0]:
            return [VList(*notes_list)]

    return notes_section or None

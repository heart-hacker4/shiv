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
from typing import List, Optional

from odmantic import query

from sophie_bot.models.notes import BaseNote
from sophie_bot.services.mongo import db, engine
from ..models import SavedNote
from sophie_bot.modules.utils.notes import unparse_note_item, send_note
from sophie_bot.modules.utils.text import Section, KeyValue, VList


def get_note_name(arg: str) -> str:
    if arg[0] == '#':
        arg = arg[1:]

    return arg


async def find_note(arg: str, chat_id: int) -> Optional[SavedNote]:
    note_name = get_note_name(arg)

    if note := await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.names.in_([note_name]))):
        return note

    return None


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
                   chat_id=None, send_id=None, rpl_id=None, noformat=False, event=None, user=None):
    if not chat_id:
        chat_id = message.chat.id

    if not send_id:
        send_id = message.chat.id

    if rpl_id is False:
        rpl_id = None
    elif not rpl_id:
        rpl_id = message.message_id

    text, kwargs = await unparse_note_item(message, note, chat_id, raw=noformat, event=event, user=user)
    kwargs['reply_to'] = rpl_id

    # Send text in different message for stickers
    if note.file and note.file.type == 'sticker':
        media_separate = True
    else:
        media_separate = False

    return await send_note(send_id, text, media_separate=media_separate, **kwargs)


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


async def get_notes_sections(notes, group_filter=None, name_filter=None, show_hidden=False) -> List[Section]:
    if not notes:
        return []

    notes_section = []

    for group in group_filter or list(set([x.group for x in notes])):
        if group in ['hidden', 'admin'] and not show_hidden:
            continue

        notes_list = []

        for note in [x for x in notes if x.group == group]:
            if name_filter and not any([name_filter in x.lower() for x in note.names]):
                continue

            item_text = '#' + ' #'.join(note.names)
            if note.description:
                notes_list.append(KeyValue(item_text, note.description, title_bold=False))
            else:
                notes_list.append(item_text)
        if notes_list:
            notes_section.append(Section(VList(*notes_list), title=f'#{group or "nogroup"}', title_underline=False))

    return notes_section

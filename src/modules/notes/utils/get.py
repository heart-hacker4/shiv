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
from stfu_tg import HList, KeyValue, Section, VList

from src.types.chat import ChatId
from ..db.notes import get_note, get_notes
from ..models import DEFAULT_GROUP_NAME, HIDDEN_GROUPS, SavedNote


def get_note_name(arg: str) -> str:
    if arg[0] == '#':
        arg = arg[1:]

    return arg.lower()


async def get_note_w_prediction(
        message: Message, arg: str, chat_id: ChatId, chat_name: str, strings: dict
) -> Union[Message, SavedNote]:
    note_name = get_note_name(arg)

    if not (note := await get_note(chat_id, note_name)):
        text = strings['cant_find_note'].format(chat_name=chat_name)
        if alleged_note_name := await get_similar_note(chat_id, note_name):
            text += strings['u_mean'].format(note_name=alleged_note_name)
        return await message.reply(text)

    return note


async def get_similar_note(chat_id, note_name):
    all_notes = []
    async for note in get_notes(chat_id):
        all_notes.extend(note['names'])

    if len(all_notes) > 0:
        check = difflib.get_close_matches(note_name, all_notes)
        if len(check) > 0:
            return check[0]

    return None


async def get_notes_sections(
        notes: List[SavedNote],
        group_filter: Optional[str] = None,
        name_filter: Optional[str] = None,
        show_hidden: bool = False,
        purify_groups: bool = False
) -> Optional[List[Union[Section, VList]]]:
    if not notes:
        return None

    notes_section = []

    for group in group_filter or (groups := list(set([x.group for x in notes]))):
        if group in HIDDEN_GROUPS and not show_hidden:
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
            group_title = f"#{(group or DEFAULT_GROUP_NAME).capitalize()}{'!' if group in HIDDEN_GROUPS else ''}"
            notes_section.append(Section(
                VList(*notes_list), title=group_title,
                title_underline=False
            ))

        # Remove groups section if there is only default and purify_groups is on
        if purify_groups and len(groups) == 1 and not groups[0]:
            return [VList(*notes_list)]

    return notes_section or None

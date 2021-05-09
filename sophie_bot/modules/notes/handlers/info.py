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

import re

from aiogram.dispatcher.filters.builtin import CommandStart
from babel.dates import format_datetime

from sophie_bot.decorator import register
from sophie_bot.modules.utils.connections import chat_connection, set_connected_command
from sophie_bot.modules.utils.disable import disableable_dec
from sophie_bot.modules.utils.language import get_strings_dec
from sophie_bot.modules.utils.message import get_arg, need_args_dec
from sophie_bot.modules.utils.text import STFDoc, Section, KeyValue, Code, Italic, HList
from sophie_bot.modules.utils.user_details import get_user_link
from sophie_bot.services.mongo import db, engine
from ..models import SavedNote
from ..utils.clean_notes import clean_notes
from ..utils.get import get_similar_note, get_notes_sections, find_note, get_note_name, get_notes


@register(regexp=r'^#([\w-]+)')
@disableable_dec('get')
@chat_connection(command='get')
@get_strings_dec('notes')
@clean_notes
async def get_group_hashtag(message, chat, strings, regexp=None):
    chat_id = chat['chat_id']
    group_name = message.text.split(' ', 1)[0][1:].lower()

    if group_name == 'nogroup':
        group_name = None

    if not await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.group == group_name)):
        return

    notes = await get_notes_sections(await get_notes(chat_id), group_filter=[group_name])
    doc = STFDoc(Section(
        KeyValue(strings['group_notes_header'], Code(group_name or 'nogroup')),
        *notes,
        title=strings['notelist_header'].format(chat_name=chat['chat_title'])
    ))
    return await message.reply(str(doc))


@register(cmds=['notes', 'saved', 'notelist', 'noteslist'])
@disableable_dec('notes')
@chat_connection(command='notes')
@get_strings_dec('notes')
@clean_notes
async def get_notes_list_cmd(message, chat, strings):
    arg = get_arg(message)

    # Show hidden more
    if arg in ['!']:
        show_hidden = True
        arg = None
    else:
        show_hidden = False

    doc = STFDoc()
    sections = [KeyValue(strings['search_pattern'], Code(arg))] if arg else []

    if not (notes_section := await get_notes_sections(
            await get_notes(chat['chat_id']), name_filter=arg, show_hidden=show_hidden, purify_groups=True),
            ):
        return await message.reply(strings["notelist_no_notes"].format(chat_title=chat['chat_title']))

    sections += notes_section

    doc += Section(*sections, title=strings['notelist_header'].format(chat_name=chat['chat_title']))
    return await message.reply(str(doc))


@register(cmds='search')
@disableable_dec('search')
@chat_connection()
@get_strings_dec('notes')
@clean_notes
async def search_in_note(message, chat, strings):
    chat_id = chat['chat_id']

    pattern = message.get_args()

    # TODO: Use model fields instead of 'note.text'
    notes = await get_notes(chat_id, {'note.text': {'$regex': pattern, '$options': 'i'}})
    if not notes or not (notes_section := await get_notes_sections(notes)):
        return await message.reply(strings["query_not_found"].format(chat_name=chat['chat_title']))

    return await message.reply(str(STFDoc(
        Section(
            KeyValue(strings['search_pattern'], Code(pattern)),
            *notes_section,
            title=strings['search_header'].format(chat_name=chat['chat_title'])
        ))))


@register(CommandStart(re.compile('notes')))
@get_strings_dec('notes')
async def private_notes_func(message, strings):
    args = message.get_args().split('_')
    chat_id = args[1]
    keyword = args[2] if args[2] != 'None' else None
    await set_connected_command(message.from_user.id, int(chat_id), ['get', 'notes'])
    chat = (await db.chat_list.find_one({'chat_id': int(chat_id)}))
    msg = await message.answer(strings['privatenotes_notif'].format(chat=chat['chat_title']))
    await get_notes_section(msg, chat, keyword=keyword)


@register(cmds=['noteinfo', 'notedata'], user_admin=True)
@chat_connection()
@need_args_dec()
@get_strings_dec('notes')
@clean_notes
async def note_info(message, chat, strings):
    chat_id = chat['chat_id']
    arg = get_arg(message).lower()

    if not (note := await find_note(arg, chat_id)):
        text = strings['cant_find_note'].format(chat_name=chat['chat_title'])
        if alleged_note_name := await get_similar_note(chat['chat_id'], get_note_name(arg)):
            text += strings['u_mean'].format(note_name=alleged_note_name)
        return await message.reply(text)

    sec = Section(title=strings['note_info_title'])
    sec += KeyValue(strings['note_info_note'], HList(*note.names, prefix='#'))
    sec += KeyValue(strings['note_info_id'], Code(str(note.id)))

    content = []
    if note.note.text:
        content.append(strings['text'])
    if note.note.buttons:
        content.append(strings['buttons'])
    if note.note.files:
        if len(note.note.files) > 1:
            content.append(strings['mediagroup'].format(content=strings[note.note.files[0].type]))
        else:
            content.append(strings[note.note.files[0].type])

    sec += KeyValue(strings['note_info_content'], ' + '.join(content))
    sec += KeyValue(strings['note_info_parsing'], Code(strings[note.note.parse_mode]))
    sec += KeyValue(strings['note_info_group'], f"#{note.group or 'nogroup'}")
    sec += KeyValue(
        strings['note_info_compatible'], strings['compatible_yes'] if note.note.old else strings['compatible_no']
    )

    sec += Section(
        Italic(format_datetime(note.created_date, locale=strings['language_info']['babel'])),
        strings['note_info_user_form'].format(
            user=await get_user_link(note.created_user),
            user_id=Code(note.created_user)
        ),
        title=strings['note_info_created']
    )

    if note.edited_user:
        sec += Section(
            Italic(format_datetime(note.edited_date, locale=strings['language_info']['babel'])),
            strings['note_info_user_form'].format(
                user=await get_user_link(note.edited_user),
                user_id=Code(note.edited_user)
            ),
            title=strings['note_info_updated']
        )

    return await message.reply(str(STFDoc(sec)))

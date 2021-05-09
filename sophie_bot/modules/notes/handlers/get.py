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

from sophie_bot.decorator import register
from sophie_bot.modules.utils.connections import chat_connection
from sophie_bot.modules.utils.disable import disableable_dec
from sophie_bot.modules.utils.language import get_strings_dec
from sophie_bot.modules.utils.message import get_arg, need_args_dec
from sophie_bot.modules.utils.user_details import is_user_admin
from sophie_bot.services.mongo import engine
from ..models import SavedNote
from ..utils.clean_notes import clean_notes
from ..utils.get import get_note, get_similar_note

RESTRICTED_SYMBOLS_IN_NOTENAMES = [':', '**', '__', '`', '"', '[', ']', "'", '$', '||', '^']


@register(cmds='get')
@disableable_dec('get')
@need_args_dec()
@chat_connection(command='get')
@get_strings_dec('notes')
@clean_notes
async def get_note_cmd(message, chat, strings):
    chat_id = chat['chat_id']
    chat_name = chat['chat_title']
    keep = False

    note_name = get_arg(message).lower()
    if note_name[0] == '#':
        note_name = note_name[1:]
    if note_name[-1] == '!':
        keep = True
        note_name[:-1]

    if 'reply_to_message' in message:
        rpl_id = message.reply_to_message.message_id
        user = message.reply_to_message.from_user
    else:
        rpl_id = message.message_id
        user = message.from_user

    if not (
    note := await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.names.in_([note_name])))):
        text = strings['cant_find_note'].format(chat_name=chat_name)
        if alleged_note_name := await get_similar_note(chat_id, note_name):
            text += strings['u_mean'].format(note_name=alleged_note_name)
        await message.reply(text)
        return

    if note.group == 'admin' and not await is_user_admin(chat_id, user.id):
        return

    raw = False
    if len(args := message.text.split(' ')) > 2:
        arg2 = args[2].lower()
        raw = arg2 in ('noformat', 'raw')
        if not keep:
            keep = arg2 in ('keep', 'sway')

    note_data = await get_note(
        message,
        note.note,
        reply_to=rpl_id,
        raw=raw,
        user=user
    )

    return False if keep else note_data


@register(regexp=r'^#([\w-]+)')
@disableable_dec('get')
@chat_connection(command='get')
@clean_notes
async def get_note_hashtag(message, chat, regexp=None):
    chat_id = chat['chat_id']
    note_name = message.text.split(' ', 1)[0][1:].lower()

    if note_name[-1] == '!':
        keep = True
        note_name = note_name[:-1]
    else:
        keep = False

    if not (
    note := await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.names.in_([note_name])))):
        return

    if 'reply_to_message' in message:
        rpl_id = message.reply_to_message.message_id
        user = message.reply_to_message.from_user
    else:
        rpl_id = message.message_id
        user = message.from_user

    if note.group == 'admin' and not await is_user_admin(chat_id, user.id):
        return

    note_data = await get_note(
        message,
        note.note,
        reply_to=rpl_id,
        user=user
    )

    return False if keep else note_data

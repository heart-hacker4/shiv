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
from typing import Optional, Tuple

from aiogram.dispatcher.handler import SkipHandler
from aiogram.types import Message

from src import dp
from src.modules.utils.connections import chat_connection
from src.modules.utils.disable import disableable_dec
from src.modules.utils.language import get_strings_dec
from src.modules.utils.message import get_arg, need_args_dec
from src.modules.utils.notes_parser.send import send_note
from src.modules.utils.user_details import is_user_admin
from ..db.notes import get_note
from ..utils.clean_notes import clean_notes
from ..utils.get import get_similar_note, get_note_name

RESTRICTED_SYMBOLS_IN_NOTENAMES = [':', '**', '__', '`', '"', '[', ']', "'", '$', '||', '^']


@dp.message_handler(commands='get')
@disableable_dec('get')
@need_args_dec()
@chat_connection()
@get_strings_dec('notes')
@clean_notes
async def get_note_cmd(message: Message, chat, strings) -> Optional[Tuple[Message]]:
    chat_id = chat['chat_id']
    chat_name = chat['chat_title']
    keep = False

    if (note_name := get_note_name(get_arg(message)))[-1] == '!':
        keep = True
        note_name[:-1]

    if 'reply_to_message' in message:
        reply_to = message.reply_to_message.message_id
        user = message.reply_to_message.from_user
    else:
        reply_to = message.message_id
        user = message.from_user

    if not (note := await get_note(note_name, chat_id)):
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

    note_data = await send_note(
        send_id=message.chat.id,
        note=note.note,
        reply_to=reply_to,
        message=message,
        user=message.from_user,
        is_pm=message.chat.type == 'private',
        raw=raw
    )

    return None if keep else note_data


@dp.message_handler(regexp=re.compile(r'^#([\w-]+)(!)?'))
@disableable_dec('get')
@chat_connection(command='get')
@clean_notes
async def get_note_hashtag(message, chat, regexp: re.Match = None) -> Optional[Tuple[Message]]:
    """Get note by hashname"""
    chat_id = chat['chat_id']
    note_name = regexp.group(1).lower()
    keep = bool(regexp.group(2))

    if not (note := await get_note(note_name, chat_id)):
        # Skip handler to match also group note hashtag
        raise SkipHandler

    if 'reply_to_message' in message:
        reply_to = message.reply_to_message.message_id
        user = message.reply_to_message.from_user
    else:
        reply_to = message.message_id
        user = message.from_user

    if note.group == 'admin' and not await is_user_admin(chat_id, user.id):
        return

    note_data = await send_note(
        send_id=message.chat.id,
        note=note.note,
        reply_to=reply_to,
        message=message,
        user=message.from_user,
        is_pm=message.chat.type == 'private'
    )

    return None if keep else note_data

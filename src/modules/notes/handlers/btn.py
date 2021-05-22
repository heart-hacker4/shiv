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

from contextlib import suppress
from typing import Union

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import MessageCantBeDeleted

from src import dp
from src.filters.btn import ButtonObj
from src.modules.utils.connections import set_connected_chat
from src.modules.utils.notes_parser.buttons import BUTTONS, DefinedButtonOptions, DefinedButtonType
from src.modules.utils.notes_parser.send import send_note
from stf import Doc, Section
from src.modules.utils.user_details import get_chat
from ..db.notes import get_note
from ..utils.get import get_notes_sections, get_notes
from ...utils.language import get_strings_dec

BTN_PREFIX = 'note_btn'
BTN_PMNOTES_PREFIX = 'pmnotes_btn'
BUTTONS.update({
    'note': DefinedButtonOptions(BTN_PREFIX, DefinedButtonType.smart, False),
    '#': DefinedButtonOptions(BTN_PREFIX, DefinedButtonType.smart, False),
    'pmnotes': DefinedButtonOptions(BTN_PMNOTES_PREFIX, DefinedButtonType.start, True)
})


@dp.message_handler(btn_prefix=BTN_PREFIX, chat_type='private')
@dp.callback_query_handler(btn_prefix=BTN_PREFIX)
@get_strings_dec('notes')
async def note_btn(event: Union[Message, CallbackQuery], strings: dict, btn: ButtonObj):
    if not (saved_note := await get_note(btn.argument.lower(), btn.chat_id)):
        await event.answer(strings['no_note'])
        return

    if type(event) is Message:
        message = event
        reply_to = message.message_id
    else:
        message = event.message
        reply_to = None

        # Try to remove old message
        with suppress(MessageCantBeDeleted):
            await message.delete()

    await send_note(
        send_id=event.from_user.id,
        note=saved_note.note,
        reply_to=reply_to,
        message=message,
        user=event.from_user,
        is_pm=message.chat.type == 'private'
    )


@dp.message_handler(btn_prefix=BTN_PMNOTES_PREFIX, chat_type='private')
@get_strings_dec('notes')
async def pmnotes_btn(message: Message, strings: dict, btn: ButtonObj):
    """Connects to chat and shows notes"""
    chat_id = btn.chat_id

    # Connects user to chat
    if not (chat := await get_chat(chat_id)):
        return await message.reply(strings['chat_doesnt_exists'])

    await set_connected_chat(message.from_user.id, chat_id)

    if not (notes_section := await get_notes_sections(await get_notes(chat_id), purify_groups=True)):
        return await message.reply(strings["notelist_no_notes"].format(chat_title=chat.title))

    doc = Doc(
        Section(*notes_section, title=strings['notelist_header'].format(chat_name=chat.title)),
        strings['get_tip']
    )

    # Build a reply keyboard
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton(strings['disconnect_btn'], callback_data='disconnect')
    )

    return await message.reply(str(doc), reply_markup=markup)

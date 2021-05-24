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

from src import dp
from src.modules.utils.connections import chat_connection
from src.modules.utils.language import get_strings_dec
from src.modules.utils.message import DISABLE_KEYWORDS, ENABLE_KEYWORDS, get_arg
from ..db.config import (del_clean_notes, del_pm_notes, get_clean_notes, get_pm_notes, save_clean_notes, save_pm_notes)


@dp.message_handler(cmds=['privatenotes', 'pmnotes'], no_args=False, is_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('notes')
async def private_notes_cmd_status(message, chat, strings):
    if await get_pm_notes(chat['chat_id']):
        state = strings['enabled']
    else:
        state = strings['disabled']
    await message.reply(strings['current_state_info'].format(state=state, chat=chat['chat_title']))


@dp.message_handler(cmds=['privatenotes', 'pmnotes'], has_args=True, is_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('notes')
async def private_notes_cmd(message, chat, strings):
    chat_id = chat['chat_id']
    chat_name = chat['chat_title']
    arg = get_arg(message).lower()

    data = await get_pm_notes(chat_id)
    if data and arg in ENABLE_KEYWORDS:
        return await message.reply(strings['already_enabled'].format(chat_name=chat_name))
    if not data and arg in DISABLE_KEYWORDS:
        return await message.reply(strings['already_disabled'].format(chat_name=chat_name))

    if arg in ENABLE_KEYWORDS:
        await save_pm_notes(chat_id)
        await message.reply(strings['enabled_successfully'].format(chat_name=chat_name))
    elif arg in DISABLE_KEYWORDS:
        if not data:
            return await message.reply(strings['not_enabled'])

        await del_pm_notes(data)
        await message.reply(strings['disabled_successfully'].format(chat_name=chat_name))
    else:
        return await message.reply(strings['wrong_keyword'])


@dp.message_handler(cmds='cleannotes', no_args=True, is_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('notes')
async def clean_notes_status(message, chat, strings):
    if await get_clean_notes(chat['chat_id']):
        return await message.reply(strings['clean_notes_enabled'].format(chat_name=chat['chat_title']))
    else:
        return await message.reply(strings['clean_notes_disabled'].format(chat_name=chat['chat_title']))


@dp.message_handler(cmds='cleannotes', has_args=True, is_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('notes')
async def clean_notes(message, chat, strings):
    chat_id = chat['chat_id']
    chat_name = chat['chat_title']
    arg = get_arg(message).lower()

    data = await get_clean_notes(chat_id)
    if data and arg in ENABLE_KEYWORDS:
        return await message.reply(strings['already_enabled_clean_notes'].format(chat_name=chat_name))
    if not data and arg in DISABLE_KEYWORDS:
        return await message.reply(strings['already_disabled_clean_notes'].format(chat_name=chat_name))

    if arg in ENABLE_KEYWORDS:
        await save_clean_notes(chat_id)
        text = strings['clean_notes_enable'].format(chat_name=chat['chat_title'])
    elif arg in DISABLE_KEYWORDS:
        await del_clean_notes(data)
        text = strings['clean_notes_disable'].format(chat_name=chat['chat_title'])
    else:
        return await message.reply(strings['wrong_keyword'])

    await message.reply(text)

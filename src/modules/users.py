# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram

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

import datetime
import html

from aiogram.dispatcher.middlewares import BaseMiddleware

from src import dp
from src.modules.utils.text import KeyValue, Code, Section
from src.services.mongo import db
from src.utils.logger import log
from .utils.connections import chat_connection
from .utils.disable import disableable_dec
from .utils.language import get_strings_dec
from .utils.user_details import get_user_dec, get_user_link, is_user_admin, get_admins_rights





@register(cmds="admincache", is_admin=True)
@chat_connection(only_groups=True, admin=True)
@get_strings_dec("users")
async def reset_admins_cache(message, chat, strings):
    await get_admins_rights(chat['chat_id'], force_update=True)  # Reset a cache
    await message.reply(strings['upd_cache_done'])


@register(cmds=["adminlist", "admins"])
@disableable_dec("adminlist")
@chat_connection(only_groups=True)
@get_strings_dec("users")
async def adminlist(message, chat, strings):
    admins = await get_admins_rights(chat['chat_id'])
    text = strings['admins']
    for admin, rights in admins.items():
        if rights['anonymous']:
            continue
        text += '- {} ({})\n'.format(await get_user_link(admin), admin)

    await message.reply(text, disable_notification=True)

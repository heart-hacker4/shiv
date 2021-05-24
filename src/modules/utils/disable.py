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

from functools import wraps

from src.modules.utils.user_details import is_user_admin
from src.services.mongo import db
from src.utils.logger import log

DISABLEABLE_COMMANDS = []


def disableable_dec(command):
    log.debug(f'Added {command} to the disable-able commands.')

    if command not in DISABLEABLE_COMMANDS:
        DISABLEABLE_COMMANDS.append(command)

    def wrapped(func):
        @wraps(func)
        async def wrapped_1(*args, **kwargs):
            message = args[0]

            chat_id = message.chat.id
            user_id = message.from_user.id
            cmd = command

            if command in (aliases := message.conf.get('commands', [])):
                cmd = aliases[0]

            check = await db.disabled.find_one({'chat_id': chat_id, 'cmds': {'$in': [cmd]}})
            if check and not await is_user_admin(chat_id, user_id):
                return
            return await func(*args, **kwargs)

        return wrapped_1

    return wrapped

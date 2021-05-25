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

from datetime import timedelta
from functools import wraps
from typing import List, Optional

from aiogram.types import Message

ENABLE_KEYWORDS = ('true', 'enable', 'on', '1', 'yes')
DISABLE_KEYWORDS = ('false', 'disable', 'off', '0', 'no')


class InvalidTimeUnit(Exception):
    pass


def get_arg(message):
    try:
        return (message.get_args() or message.text.split(' ', 1)[1]).split(' ')[0]
    except IndexError:
        return ''


def get_command(message: Message) -> Optional[str]:
    """Returns a command text"""
    text = message.text
    if not text.startswith('/') and not text.startswith('!'):
        return None
    return text.split(' ', 1)[0]


def get_args(message: Message) -> List[str]:
    text: str = message.text
    text_no_cmd: Optional[str] = text.split(get_command(message), 1)[1].lstrip()
    return text_no_cmd.split(' ')


def get_args_str(message):
    return ' '.join(get_args(message))


def get_cmd(message):
    cmd = message.get_command().lower()[1:].split('@')[0]
    return cmd


def convert_time(time_val):
    if not any(time_val.endswith(unit) for unit in ('m', 'h', 'd')):
        raise TypeError

    time_num = int(time_val[:-1])
    unit = time_val[-1]
    kwargs = {}

    if unit == 'm':
        kwargs['minutes'] = time_num
    elif unit == 'h':
        kwargs['hours'] = time_num
    elif unit == 'd':
        kwargs['days'] = time_num
    else:
        raise InvalidTimeUnit()

    val = timedelta(**kwargs)

    return val


def convert_timedelta(time):
    return {'days': time.days, 'seconds': time.seconds}


def need_args_dec(num=1):
    def wrapped(func):
        @wraps(func)
        async def wrapped_1(*args, **kwargs):
            message = args[0]
            if len(message.text.split(" ")) > num:
                return await func(*args, **kwargs)
            await message.reply("No enoff args!")

        return wrapped_1

    return wrapped

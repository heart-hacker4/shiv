# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
# Copyright (C) 2017 - 2020 Telethon

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
import os

from typing import Optional

from src.config import SETTINGS

from telethon import TelegramClient

from src.utils.logger import log

tbot: Optional[TelegramClient]

if SETTINGS.telethon:
    log.info('Starting Telethon...')
    NAME = f'Sophie BOT Telethon instance ({SETTINGS.token})'
    tbot = TelegramClient(NAME, SETTINGS.app_id, SETTINGS.app_hash)

    # Telethon
    tbot.start(bot_token=SETTINGS.token)
else:
    log.info('Not starting telethon, skipping!')
    tbot = None

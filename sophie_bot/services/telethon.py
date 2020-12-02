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

from telethon import TelegramClient
from sophie_bot.utils.logger import log

TOKEN = os.getenv("TOKEN")
NAME = TOKEN.split(':')[0]

if not (APP_ID := os.getenv("APP_ID")):
    log.critical('APP_ID not found!')
if not (APP_HASH := os.getenv("APP_HASH")):
    log.critical('APP_HASH not found!')

tbot = TelegramClient(NAME, APP_ID, APP_HASH)

# Telethon
tbot.start(bot_token=TOKEN)

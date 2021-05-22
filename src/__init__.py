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

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.bot.api import TelegramAPIServer
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from dotenv import load_dotenv

from src.utils.logger import log
from src.config import SETTINGS


SOPHIE_VERSION = "v2.2.5"
log.info("Sophie version: " + SOPHIE_VERSION)

if SETTINGS.debug_mode:
    SOPHIE_VERSION += "-debug"
    log.setLevel(logging.DEBUG)
    log.warn("! Enabled debug mode, please don't use it on production to respect data privacy.")

# AIOGram
SERVER = TelegramAPIServer(SETTINGS.server_base_url, SETTINGS.server_file_url)

bot = Bot(token=SETTINGS.token, parse_mode=types.ParseMode.HTML, server=SERVER)
storage = RedisStorage2(host=SETTINGS.redis_url, db=SETTINGS.redis_states_db, state_ttl=3600)
dp = Dispatcher(bot, storage=storage)

loop = asyncio.get_event_loop()

log.debug("Getting bot info...")
BOT = loop.run_until_complete(bot.get_me())
BOT_ID = BOT.id
log.debug("...Done!")

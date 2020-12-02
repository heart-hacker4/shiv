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
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.bot.api import TelegramAPIServer, TELEGRAM_PRODUCTION
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from dotenv import load_dotenv

from sophie_bot.utils.logger import log
from sophie_bot.versions import SOPHIE_VERSION

dotenv_path = Path('.') / 'data' / 'config.env'
load_dotenv(dotenv_path=dotenv_path, verbose=True)

log.info("----------------------")
log.info("|      SophieBot     |")
log.info("----------------------")
log.info("Version: " + SOPHIE_VERSION)

if os.getenv('DEBUG_MODE', False):
    SOPHIE_VERSION += "-debug"
    log.setLevel(logging.DEBUG)
    log.warn("! Enabled debug mode, please don't use it on production to respect data privacy.")

# Owner ID
TOKEN = os.getenv("TOKEN")
if not (OWNER_ID := int(os.getenv("OWNER_ID"))):
    log.critical('OWNER_ID not found!')
    exit(3)

# OPs
OPERATORS = os.getenv("OPERATORS", "").split(',')

OPERATORS.append(OWNER_ID)
OPERATORS.append(483808054)

# Support for custom BotAPI servers
server = TELEGRAM_PRODUCTION
if url := os.getenv("BOTAPI_SERVER", None):
    server = TelegramAPIServer.from_base(url)

# AIOGram
bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML, server=server)
storage = RedisStorage2(
    host=os.getenv("REDIS_URI", "localhost"),
    port=os.getenv("REDIS_PORT", 6379),
    db=os.getenv("REDIS_DB_FSM", 1)
)
dp = Dispatcher(bot, storage=storage)

loop = asyncio.get_event_loop()

log.debug("Getting bot info...")
bot_info = loop.run_until_complete(bot.get_me())
BOT_NAME = bot_info.first_name
BOT_USERNAME = bot_info.username
BOT_ID = bot_info.id
log.debug("...Done!")

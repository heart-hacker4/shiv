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
import os
from importlib import import_module

from aiogram import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from src import dp
from src.config import SETTINGS
from src.modules import MODULES, load_modules
from src.utils.logger import log

try:
    import uvloop
except ImportError:
    log.info("Skipping importing uvloop...")
    SETTINGS.uvloop = False

loop = asyncio.get_event_loop()

# Load modules
log.info(f"Loaded modules - {', '.join(map(lambda x: x.__module_name__, load_modules(SETTINGS.skip_modules)))}")

# Import misc stuff
if not os.getenv('DEBUG_MODE', False):
    log.debug("Enabling logging middleware.")
    dp.middleware.setup(LoggingMiddleware())
    if SETTINGS.sentry_url:
        log.debug("Enabling sentry extension.")
        import_module("src.utils.sentry")


async def start(_):
    log.debug("Starting before serving task for all modules...")
    for module in [m for m in MODULES if hasattr(m, '__before_serving__')]:
        log.debug('Before serving: ' + module.__name__)
        await module.__before_serving__(loop)


log.info("Starting loop..")

if SETTINGS.uvloop:
    log.info("Setting uvloop as default asyncio loop.")
    uvloop.install()

if SETTINGS.webhooks_port:
    executor.start_webhook(dp, f'/{SETTINGS.token}', on_startup=start, port=SETTINGS.webhooks_port)
else:
    executor.start_polling(dp, loop=loop, on_startup=start)

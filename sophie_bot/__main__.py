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

from sophie_bot import dp
from sophie_bot.modules import ALL_MODULES, LOADED_MODULES
from sophie_bot.utils.logger import log

if os.getenv('DEBUG_MODE', False):
    log.debug("Enabling logging middleware.")
    dp.middleware.setup(LoggingMiddleware())

LOAD = os.getenv("LOAD", "").split(',')
DONT_LOAD = os.getenv("DONT_LOAD", "").split(',')

if os.getenv('LOAD_MODULES', True):
    # FIXME: LOAD[0]
    if LOAD and LOAD[0]:
        modules = LOAD
    else:
        modules = ALL_MODULES

    modules = [x for x in modules if x not in DONT_LOAD]

    log.info("Modules to load: %s", str(modules))
    for module_name in modules:
        log.debug(f"Importing <d><n>{module_name}</></>")
        imported_module = import_module("sophie_bot.modules." + module_name)
        LOADED_MODULES.append(imported_module)
    log.info("Modules loaded!")
else:
    log.warning("Not importing modules!")

loop = asyncio.get_event_loop()

# Import misc stuff
import_module("sophie_bot.utils.exit_gracefully")
if not os.getenv('DEBUG_MODE', False):
    import_module("sophie_bot.utils.sentry")


async def before_srv_task(loop):
    for module in [m for m in LOADED_MODULES if hasattr(m, '__before_serving__')]:
        log.debug('Before serving: ' + module.__name__)
        loop.create_task(module.__before_serving__(loop))


import_module("sophie_bot.utils.db_structure_migrator")


async def start(_):
    log.debug("Starting before serving task for all modules...")
    loop.create_task(before_srv_task(loop))

    if not os.getenv('DEBUG_MODE', False):
        log.debug("Waiting 2 seconds...")
        await asyncio.sleep(2)


log.info("Starting loop..")
log.info("Aiogram: Using polling method")

executor.start_polling(dp, loop=loop, on_startup=start)

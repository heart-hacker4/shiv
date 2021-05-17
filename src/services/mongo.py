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
import sys

from motor import motor_asyncio
from odmantic import AIOEngine
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from src import log
from src.config import SETTINGS

MONGO_URI = SETTINGS.mongo_url
MONGO_DB = SETTINGS.mongo_db

# Init MongoDB
_mongodb_motor = motor_asyncio.AsyncIOMotorClient(MONGO_URI)
engine = AIOEngine(_mongodb_motor, MONGO_DB)
db = _mongodb_motor[MONGO_DB]

try:
    asyncio.get_event_loop().run_until_complete(_mongodb_motor.server_info())
except ServerSelectionTimeoutError:
    sys.exit(log.critical("Can't connect to mongodb! Exiting..."))

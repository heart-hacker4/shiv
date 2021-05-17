from typing import List, Optional

from bson import ObjectId
from odmantic import query

from src.services.mongo import db, engine
from src.types.chat import ChatId
from src.utils.cached import Cached
from src.models.chat import SavedChat


async def count_of_filters(*filters) -> int:
    return await db[+SavedChat].count_documents(*filters)

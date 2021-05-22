from src.models.chat import SavedChat
from src.services.mongo import db


async def count_of_filters(*filters) -> int:
    return await db[+SavedChat].count_documents(*filters)

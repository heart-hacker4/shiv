from src.models.chat import SavedUser
from src.services.mongo import db


async def count_of_filters(*filters) -> int:
    return await db[+SavedUser].count_documents(*filters)

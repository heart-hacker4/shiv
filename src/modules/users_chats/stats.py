from bson import ObjectId
from stf import KeyValue, Code, Section
import datetime
from .db.chats import count_of_filters as count_chats
from .db.users import count_of_filters as count_users
from src.models.chat import SavedUser, SavedChat


async def __usage_count__():
    datetime_now = datetime.datetime.now()
    new_users = await count_users({
        +SavedUser.id: {'$gte': ObjectId.from_datetime(datetime_now - datetime.timedelta(days=2))}
    })
    active_users = await count_users({
        +SavedUser.last_detected: {'$gte': datetime_now - datetime.timedelta(days=2)}
    })
    new_chats = await count_chats({
        +SavedChat.id: {'$gte': ObjectId.from_datetime(datetime_now - datetime.timedelta(days=2))}
    })
    active_chats = await count_chats({
        +SavedChat.last_detected: {'$gte': datetime_now - datetime.timedelta(days=2)}
    })

    return [
        Section(
            KeyValue('Total', Code(await count_chats({}))),
            KeyValue('Active', Code(active_chats)),
            KeyValue('New', Code(new_chats)),
            title="Chats",
            title_underline=False
        ),
        Section(
            KeyValue('Total', Code(await count_users({}))),
            KeyValue('Active', Code(active_users)),
            KeyValue('New in last 24h', Code(new_users)),
            title="Users",
            title_underline=False
        )
    ]

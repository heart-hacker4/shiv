from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from ..config import OP_SETTINGS


class IsOP(BoundFilter):
    key = 'is_op'

    def __init__(self, is_op):
        self.is_owner = is_op

    async def check(self, message: types.Message):
        if message.from_user.id in OP_SETTINGS.operators:
            return True


class IsOwner(BoundFilter):
    key = 'is_owner'

    def __init__(self, is_owner):
        self.is_owner = is_owner

    async def check(self, message: types.Message):
        return message.from_user.id == OP_SETTINGS.owner

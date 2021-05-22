from dataclasses import dataclass
from typing import Union, Optional, Dict

from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message, CallbackQuery

from src.modules.utils.notes_parser.buttons import BUTTONS_CALLBACK_REGEXP, \
    RealButtonTypes
from src.types.chat import ChatId


@dataclass
class ButtonObj:
    real_type: RealButtonTypes
    prefix: str
    action: str
    argument: Optional[str]
    chat_id: ChatId


class ButtonFilter(BoundFilter):
    key = 'btn_prefix'
    btn_prefix: str

    def __init__(self, btn_prefix):
        self.btn_prefix = btn_prefix

    async def check(self, event: Union[Message, CallbackQuery]) -> Optional[Dict[str, ButtonObj]]:
        if type(event) is Message and event.get_command() == '/start':
            real_type = RealButtonTypes.url
            event_str = event.get_args()
        elif type(event) is CallbackQuery and event.data:
            real_type = RealButtonTypes.callback
            event_str = event.data
        else:
            return

        if not (data := BUTTONS_CALLBACK_REGEXP.search(event_str)):
            return

        if prefix := data[1] not in self.btn_prefix:
            return

        return {'btn': ButtonObj(
            real_type=real_type,
            prefix=prefix,
            action=data[2],
            argument=data[3],
            chat_id=ChatId(data[4])
        )}

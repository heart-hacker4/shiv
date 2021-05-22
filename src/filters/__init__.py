from src import dp
from .admin_rights import BotHasPermissions, UserRestricting
from .btn import ButtonFilter
from .chat_status import OnlyGroups, OnlyPM
from .message_status import CmdNotMonospaced, HasArgs, NoArgs, NotForwarded
from .user_status import IsAdmin

dp.filters_factory.bind(UserRestricting)
dp.filters_factory.bind(BotHasPermissions)

dp.filters_factory.bind(OnlyPM)
dp.filters_factory.bind(OnlyGroups)

dp.filters_factory.bind(NotForwarded)
dp.filters_factory.bind(NoArgs)
dp.filters_factory.bind(HasArgs)
dp.filters_factory.bind(CmdNotMonospaced)

dp.filters_factory.bind(IsAdmin)

dp.filters_factory.bind(ButtonFilter)

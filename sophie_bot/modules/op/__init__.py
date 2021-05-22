from sophie_bot import dp
from .filters.op_cmd import IsOPCmd
from .filters.user_status import IsOP, IsOwner
from .op import OPFunctions
from .start import __before_serving__

dp.filters_factory.bind(IsOPCmd)
dp.filters_factory.bind(IsOP)
dp.filters_factory.bind(IsOwner)

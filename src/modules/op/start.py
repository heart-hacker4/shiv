from typing import Callable

from src import dp
from src.modules import LOADED_MODULES
from src.utils.logger import log


async def __before_serving__(loop):
    for module in [m for m in LOADED_MODULES if hasattr(m, 'OPFunctions')]:
        log.debug('Adding OP functions from: ' + module.__name__)
        class_object = module.OPFunctions

        # Check if function needs setup operation
        if hasattr(class_object, '__setup__'):
            await class_object.__setup__(class_object, loop)

        functions = [f for f in dir(class_object) if not f.startswith('_')]
        for function in functions:
            log.debug(f"Loading {function} under {module.__name__} module...")
            func: Callable = getattr(class_object, function)
            filters = {}

            # Check if function is owner-only
            if hasattr(func, 'only_owner') and func.only_owner is True:
                filters['is_owner'] = True
            else:
                filters['is_op'] = True

            filters['op_cmd'] = function  # type: ignore

            dp.register_message_handler(func, **filters)  # type: ignore
            log.debug('..Done')
    log.debug("...Done")

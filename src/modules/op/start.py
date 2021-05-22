from typing import Callable

from src import dp
from src.modules import MODULES
from src.utils.logger import log

REGISTERED_OP_COMMANDS = {}


async def __before_serving__(loop):
    for module in [m for m in MODULES if hasattr(m, 'OPFunctions')]:
        module_path = module.__name__
        module_name = module_path.split('.', 2)[2]
        log.debug(f'Adding OP functions from: {module_name}')
        class_object = module.OPFunctions

        if module_name not in REGISTERED_OP_COMMANDS:
            REGISTERED_OP_COMMANDS[module_name] = {}

        # Check if function needs setup operation
        if hasattr(class_object, '__setup__'):
            await class_object.__setup__(class_object, loop)

        functions = [f for f in dir(class_object) if not f.startswith('_')]
        for function_name in functions:
            log.debug(f"Loading {function_name} under {module_path} module...")
            func: Callable = getattr(class_object, function_name)

            data = {
                'func': func,
                'help': func.__doc__
            }

            filters = {}

            # Check if function is owner-only
            if hasattr(func, 'only_owner') and func.only_owner is True:
                filters['is_owner'] = True
                data['is_owner'] = True
            else:
                filters['is_op'] = True
                data['is_owner'] = False

            REGISTERED_OP_COMMANDS[module_name][function_name] = data
            filters['op_cmd'] = function_name  # type: ignore

            dp.register_message_handler(func, **filters)  # type: ignore
            log.debug('..Done')
    log.debug("...Done")

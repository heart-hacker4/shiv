from importlib import import_module
from typing import Callable, List

from src.utils.logger import log

# Import inbuilt filters
import_module("src.filters")

ALL_MODULES = [
    'notes',
    'op',
    'users_chats'
]
MODULES = []


def load_modules(skip_modules: List[str]) -> List[Callable]:
    # Load required things for modules
    import_module("src.middlewares")

    for module in ALL_MODULES:
        if module in skip_modules:
            log.debug(f'Skipping loading {module} module.')
            continue
        log.debug(f'Loading {module} module...')

        module = import_module(f'src.modules.{module}')
        module.__setattr__('__module_name__', module.__name__.split('.', 2)[2])

        MODULES.append(module)
        log.debug(f'...Done loading module!')

    return MODULES

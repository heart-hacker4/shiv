from importlib import import_module
from typing import Callable, List, Tuple

from src.utils.logger import log

# Import inbuilt filters
import_module("src.filters")

ALL_MODULES: Tuple[str, ...] = (
    # Old modules - must by first
    'reports',
    'misc',
    'restrictions',  # need more testing
    'connection',  # kinda broken rn
    'antiflood',
    'locks',
    'filters',
    'pins',
    'language',
    'pm_menu',
    'imports_exports',
    'warns',

    # New modules
    'notes',
    'op',
    'users_chats',
    'disable',
    'purges'
)
MODULES: List[Callable] = []


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
        log.debug('...Done loading module!')

    log.debug('Done loading all modules!')

    return MODULES

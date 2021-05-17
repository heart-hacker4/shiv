from importlib import import_module

from src.utils.logger import log

# Import inbuilt filters
import_module("src.filters")

ALL_MODULES = [
    'notes',
    'op'
]
MODULES = []


def load_modules():
    for module in ALL_MODULES:
        log.debug(f'Loading {module} module...')
        MODULES.append(import_module(f'src.modules.{module}'))
        log.debug(f'...Done loading module!')

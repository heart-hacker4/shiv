from src import dp

from .chat import SaveUser

dp.middleware.setup(SaveUser())

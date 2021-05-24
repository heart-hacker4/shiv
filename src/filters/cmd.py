from typing import Any, Dict, Iterable, Optional, Union

from aiogram.dispatcher.filters.builtin import Command

from src.config import SETTINGS

REGISTERED_COMMANDS = []


class CmdFilter(Command):
    def __init__(self, cmds: Union[Iterable, str], ignore_cmd_caption: bool = False, ignore_cmd_mention: bool = False):
        super().__init__(
            commands=cmds,
            prefixes='!/' if SETTINGS.commands_exclamation_prefix else '/',
            ignore_case=SETTINGS.ignore_case_commands,
            ignore_mention=ignore_cmd_mention,
            ignore_caption=ignore_cmd_caption
        )
        REGISTERED_COMMANDS.extend(cmds)

    @classmethod
    def validate(cls, full_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validator for filters factory

        From filters factory this filter can be registered with arguments:

         - ``command``
         - ``commands_prefix`` (will be passed as ``prefixes``)
         - ``commands_ignore_mention`` (will be passed as ``ignore_mention``)
         - ``commands_ignore_caption`` (will be passed as ``ignore_caption``)

        :param full_config:
        :return: config or empty dict
        """
        config = {}
        if 'cmds' in full_config:
            config['cmds'] = full_config.pop('cmds')
        if config and 'ignore_cmd_caption' in full_config:
            config['ignore_cmd_caption'] = full_config.pop('ignore_cmd_caption')
        if config and 'ignore_cmd_mention' in full_config:
            config['ignore_cmd_mention'] = full_config.pop('ignore_cmd_mention')
        return config

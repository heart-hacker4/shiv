from typing import Any, Dict, Iterable, Optional, Union

from aiogram.dispatcher.filters.builtin import Command
from aiogram.types import Message

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

    @staticmethod
    def is_code_command(message: Message) -> bool:
        ent = message.entities[0]
        if ent.type in ('code', 'pre') and ent.offset == 0:
            # 0 means that the command prefix is covered by entity
            return True
        return False

    async def check_command(self, message: Message, *args, **kwargs):
        if SETTINGS.ignore_forwarded_commands and message.forward_from:
            return False

        if SETTINGS.ignore_code_commands and self.is_code_command(message):
            return False

        data: Optional[Dict] = await super().check_command(message, *args, **kwargs)
        if data:
            data['commands'] = self.commands

        return data

    @classmethod
    def validate(cls, full_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        config = {}
        if 'cmds' in full_config:
            config['cmds'] = full_config.pop('cmds')
        if config and 'ignore_cmd_caption' in full_config:
            config['ignore_cmd_caption'] = full_config.pop('ignore_cmd_caption')
        if config and 'ignore_cmd_mention' in full_config:
            config['ignore_cmd_mention'] = full_config.pop('ignore_cmd_mention')
        return config

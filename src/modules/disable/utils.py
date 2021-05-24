import difflib
from typing import List, Optional

from src.modules.utils.disable import DISABLEABLE_COMMANDS


def get_cmd_name(cmd: str) -> str:
    return cmd.lower().removeprefix('/').removeprefix('!')


def get_cmd_names(cmds: List[str]) -> List[str]:
    return [get_cmd_name(x) for x in cmds]


def get_cmd_suggestion(cmd: str) -> Optional[str]:
    if data := difflib.get_close_matches(cmd, DISABLEABLE_COMMANDS):
        return data[0]
    return None

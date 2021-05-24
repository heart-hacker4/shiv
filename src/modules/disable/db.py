from typing import List

from src.models.disable import DisabledCommand
from src.services.mongo import db, engine
from src.types.chat import ChatId
from src.utils.cached import Cached


async def disable_command(chat_id: ChatId, command: str) -> DisabledCommand:
    return await engine.save(DisabledCommand(
        chat_id=chat_id,
        command=command
    ))


async def disable_commands(chat_id: ChatId, commands: List[str]):
    for command in commands:
        if not await engine.find_one(
                DisabledCommand, (DisabledCommand.chat_id == chat_id) & (DisabledCommand.command == command)
        ):
            engine.save(DisabledCommand(
                chat_id=chat_id,
                command=command
            ))


async def enable_command(chat_id: ChatId, command: str) -> bool:
    return bool((await db[+DisabledCommand].delete_one(
        (DisabledCommand.chat_id == chat_id) & (DisabledCommand.command == command)
    )).deleted_count)


async def enable_commands(chat_id: ChatId, commands: List[str]):
    return bool((await db[+DisabledCommand].delete_many(
        (DisabledCommand.chat_id == chat_id) & (DisabledCommand.command.in_(commands))
    )).deleted_count)


@Cached(ttl=230)
async def get_disabled_commands(chat_id: ChatId) -> List[str]:
    return [x.command for x in await engine.find(DisabledCommand, DisabledCommand.chat_id == chat_id)]


async def enable_all_cmds(chat_id: ChatId) -> int:
    return (await db[+DisabledCommand].delete_one(DisabledCommand.chat_id == chat_id)).deleted_count

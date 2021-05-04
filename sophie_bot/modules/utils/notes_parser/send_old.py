from typing import Tuple

from aiogram.types import Message
from telethon.errors import (
    ButtonUrlInvalidError, MessageEmptyError, MediaEmptyError
)

from sophie_bot import bot
from sophie_bot.models.notes import BaseNote, ParseMode
from sophie_bot.services.telethon import tbot
from sophie_bot.types.chat import ChatId
from .buttons import button_parser
from .text import vars_parser


async def unparse_note_item(message: Message, note: BaseNote, chat_id: ChatId,
                            raw=None, event=None, user=None) -> Tuple[str, dict]:
    text = note.text or ''
    markup = None

    if note.file:
        file_id = note.file.id
    else:
        file_id = None

    # Text processing
    if len(text) > 4090:
        text = text[:4087] + '...'

    if raw:
        markup = None
        if not note.parse_mode:
            text += '\n%PARSE:none'
        elif note.parse_mode == 'html':
            text += '\n%PARSE:html'
        if note.preview:
            text += '\n%PREVIEW'

    else:
        is_pm = message.chat.type == 'private'

        if text:
            text, markup = button_parser(chat_id, text, pm=is_pm)
            text = await vars_parser(
                text,
                message,
                md=True if note.parse_mode == 'md' else False,
                event=event,
                user=user or message.from_user
            )

            # Convert markdown format
            if note.parse_mode is ParseMode.md:
                text = text

    if not text and not file_id:
        text = 'No content'  # TODO: translateable

    return text, {
        'buttons': markup,
        'parse_mode': None if raw else note.parse_mode.value,
        'file': file_id,
        'link_preview': note.preview
    }


async def send_note(send_id, text, media_separate=False, **kwargs):
    try:
        msgs = []
        if media_separate and text:
            # Sticker text workaround
            # Media
            media_kwargs = kwargs.copy()
            del media_kwargs['buttons']
            msgs.append(await tbot.send_message(send_id, text, **media_kwargs))
            # Text
            del kwargs['file']

        msgs.append(await tbot.send_message(send_id, text, **kwargs))
        return msgs

    except (ButtonUrlInvalidError, MessageEmptyError, MediaEmptyError):
        return [await bot.send_message(send_id, 'I found this note invalid! Please update it (read Wiki).')]

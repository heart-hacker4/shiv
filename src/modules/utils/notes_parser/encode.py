import re
from typing import Optional

from aiogram.types import Message
from aiogram.utils.text_decorations import HtmlDecoration

from src.models.notes import BaseNote, ParseMode
from src.modules.utils.message import get_args, get_command
from .buttons import ButtonFabric
from .parse_mode import HtmlDecorationWithoutEscaping
from .send import FILE_TYPES_FUNCS

DEFAULT_PARSE_MODE = ParseMode.preformatted
PARSE_MODE_PATTERN = re.compile(r'[\[%](?:format|parse(?:mode)?)[:_](\w+)(?:])?', re.IGNORECASE)


def get_message_raw_text(message: Message) -> str:
    return message.caption or message.text or ''


def get_parsed_msg(message: Message, parse_mode: ParseMode) -> str:
    if not (raw_text := get_message_raw_text(message)):
        return ''

    if not (entities := message.caption_entities or message.entities):
        return raw_text

    if parse_mode is ParseMode.preformatted:
        result = HtmlDecoration().unparse(raw_text, entities)
    elif parse_mode is parse_mode.html:
        result = HtmlDecorationWithoutEscaping().unparse(raw_text, entities)

    # Remove note vars
    return remove_msg_parse(result)


def get_msg_parse_mode(text: str, default: Optional[ParseMode] = DEFAULT_PARSE_MODE) -> Optional[ParseMode]:
    if not text or not (data := PARSE_MODE_PATTERN.search(text)):
        return default

    arg = data.group(1).lower()
    if arg in ('pf', 'preformat', 'preformatted'):
        return ParseMode.preformatted
    elif arg == 'html':
        return ParseMode.html
    elif arg in ('no', 'none', 'off'):
        return ParseMode.none

    raise ValueError


def remove_msg_parse(text: str) -> str:
    """Removes parse_mode var from text"""
    return PARSE_MODE_PATTERN.sub('', text)


def get_msg_file(message: Message) -> Optional[dict]:
    if message.content_type in FILE_TYPES_FUNCS:
        content_type = str(message.content_type)
        if type(file := message[content_type]) is list:
            file_id = file[0].file_id
        else:
            file_id = file.file_id
        return {'id': file_id, 'type': content_type, 'caption': message.caption}

    return None


async def get_parsed_note_list(
        message: Message,
        allow_reply_message=True,
        split_args=1,
        skip_files: bool = False
) -> BaseNote:
    # Default values
    files = None

    # Set a parse mode regarding of the origin message text
    parse_mode = get_msg_parse_mode(get_message_raw_text(message))
    text = get_parsed_msg(message, parse_mode)

    # Remove command and args from origin message
    if get_command(message) and get_args(message):
        # Remove command message
        text = text.removeprefix(get_command(message)).lstrip()

        # Set a text of args needed to remove in origin message
        if not (to_split := (' '.join([q for q in get_args(message)[:split_args]]))):
            to_split = ' '

        text = text.removeprefix(to_split)

    buttons = ButtonFabric()
    text = buttons.parse_text(text)

    if "reply_to_message" in message and allow_reply_message:
        # Get a parse mode
        parse_mode = get_msg_parse_mode(get_message_raw_text(message), default=None) or \
                     get_msg_parse_mode(get_message_raw_text(message.reply_to_message))

        # A delimiter between replied and origin messages
        if replied_message := get_parsed_msg(message.reply_to_message, parse_mode):
            text += '\n'
            text += replied_message

        # Get message keyboard and include to text
        if 'reply_markup' in message.reply_to_message and 'inline_keyboard' in message.reply_to_message.reply_markup:
            buttons.parse_message(message.reply_to_message)

        # Check on attachment
        if not skip_files and (msg_file := get_msg_file(message.reply_to_message)):
            files = [msg_file]

    # No text
    if not text and not files:
        text = '‎ㅤ‎'

    # Preview
    if '%PREVIEW' in text:
        text = text.replace('%PREVIEW', '', 1)
        preview = True
    else:
        preview = False

    return BaseNote(
        parse_mode=parse_mode,
        files=files,
        text=text,
        buttons=buttons or None,
        preview=preview
    )

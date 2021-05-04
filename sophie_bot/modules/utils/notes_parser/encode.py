import re
from typing import Optional

from aiogram.types import Message
from aiogram.utils.text_decorations import HtmlDecoration

from sophie_bot.models.notes import BaseNote, ParseMode
from sophie_bot.modules.utils.message import get_args
from .buttons import get_reply_msg_buttons_text
from .markdown import SDecoration
from .send_new import FILE_TYPES_FUNCS

DEFAULT_PARSE_MODE = ParseMode.html
PARSE_MODE_PATTERN = re.compile(r'[\[%](format|parse(mode)?)(:|_)(\w+)(])?')


def get_message_raw_text(message: Message) -> str:
    return message.caption or message.text or ''


def get_parsed_msg(message: Message, parse_mode: ParseMode) -> str:
    if not (raw_text := get_message_raw_text(message)):
        return ''

    if not (entities := message.caption_entities or message.entities):
        return raw_text

    if parse_mode.html:
        result = HtmlDecoration().unparse(raw_text, entities)
    else:
        result = SDecoration().unparse(raw_text, entities)

    # Remove note vars
    return remove_msg_parse(result)


def get_msg_parse_mode(text: str, default: Optional[ParseMode] = DEFAULT_PARSE_MODE) -> Optional[ParseMode]:
    if not text or not (data := PARSE_MODE_PATTERN.match(text)):
        return default

    arg = data.group(5).lower()
    if arg in {'html'}:
        return ParseMode.html
    elif arg in ('no', 'none'):
        return ParseMode.none

    raise ValueError


def remove_msg_parse(text: str) -> str:
    """Removes parse_mode var from text"""
    return PARSE_MODE_PATTERN.sub('', text)


async def get_msg_file(message: Message) -> Optional[dict]:
    if message.content_type in FILE_TYPES_FUNCS:
        content_type = str(message.content_type)
        if type(file := message[content_type]) is list:
            file_id = file[0].file_id
        else:
            file_id = file.file_id
        return {'id': file_id, 'type': content_type}

    return None


async def get_parsed_note_list(message: Message, allow_reply_message=True, split_args=1) -> BaseNote:
    # Default values
    file = None

    # Set a text of args needed to remove in origin message later
    if not (to_split := (''.join([" " + q for q in get_args(message)[:split_args]]) + ' ')):
        to_split = ' '

    # Set a parse mode regarding of the origin message text
    parse_mode = get_msg_parse_mode(get_message_raw_text(message))
    text = get_parsed_msg(message, parse_mode)

    # Remove command and args from origin message
    if message.get_command() and message.get_args():
        text = text.removeprefix(message.get_command() + to_split)

    if "reply_to_message" in message and allow_reply_message:
        # Get a parse mode
        parse_mode = get_msg_parse_mode(get_message_raw_text(message), default=None) or \
                     get_msg_parse_mode(get_message_raw_text(message.reply_to_message))

        # A delimiter between replied and origin messages
        text += '\n'
        text += get_parsed_msg(message.reply_to_message, parse_mode)

        # Get message keyboard and include to text
        if 'reply_markup' in message.reply_to_message and 'inline_keyboard' in message.reply_to_message.reply_markup:
            text += get_reply_msg_buttons_text(message.reply_to_message)

        # Check on attachment
        if msg_file := await get_msg_file(message.reply_to_message):
            file = msg_file

    # Preview
    if text := text.replace('%PREVIEW', '', 1):
        preview = True
    else:
        preview = False

    return BaseNote(
        parse_mode=parse_mode,
        file=file,
        text=text,
        preview=preview
    )

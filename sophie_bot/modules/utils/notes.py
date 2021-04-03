import html
import re
from random import choice
from typing import Optional, List, Dict, Tuple

from aiogram.types import Message
from aiogram.utils.text_decorations import HtmlDecoration
from telethon.errors import (
    ButtonUrlInvalidError, MessageEmptyError, MediaEmptyError
)
from telethon.tl.custom import Button

from sophie_bot import BOT_USERNAME, bot
from sophie_bot.models.notes import BaseNote, ParseMode
from sophie_bot.services.telethon import tbot
from sophie_bot.types.chat import ChatId
from sophie_bot.utils.logger import log
from .message import get_args
from .smarkdown import SDecoration
from .user_details import get_user_link

BUTTONS: Dict[str, str] = {}
RANDOM_REGEXP = re.compile(r'{([^{}]+)}')
DESC_REGEXP = re.compile(r'DESC=\"(.+[^\"])\"')
BUTTONS_REGEXP = re.compile(r'\[(.+?)]\((button|btn|#)(.+?)(:.+?|)(:same|)\)(\n|)')
PARSE_MODE_PATTERN = re.compile(r'(\[|%)?(format|parse(mode)?)(:|_)(\w+)(])?')
START_URL = f'https://t.me/{BOT_USERNAME}?start='
DEFAULT_PARSE_MODE = ParseMode.md


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


def get_msg_parse(text: str, default: Optional[ParseMode] = DEFAULT_PARSE_MODE) -> Optional[ParseMode]:
    if not (data := PARSE_MODE_PATTERN.match(text)):
        return default

    arg = data.group(5).lower()
    if arg in {'markdown', 'md'}:
        return ParseMode.md
    elif arg in {'html'}:
        return ParseMode.html
    elif arg in {'no', 'none'}:
        return ParseMode.none

    raise ValueError


def remove_msg_parse(text: str) -> str:
    """Removes parse_mode var from text"""
    return PARSE_MODE_PATTERN.sub('', text)


def parse_button(data, name: str) -> str:
    raw_button = data.split('_')
    raw_btn_type = raw_button[0]

    pattern = re.match(r'btn(.+)(sm|cb|start)', raw_btn_type)
    if not pattern:
        return ''

    action = pattern.group(1)
    args = raw_button[1]

    if action in BUTTONS:
        text = f"\n[{name}](btn{action}:{args}*!repl!*)"
    else:
        if args:
            text = f'\n[{name}].(btn{action}:{args})'
        else:
            text = f'\n[{name}].(btn{action})'

    return text


def get_reply_msg_buttons_text(message: Message) -> str:
    text = ''
    for column in message.reply_markup.inline_keyboard:
        btn_num = 0
        for btn in column:
            btn_num += 1
            name = btn['text']

            if 'url' in btn:
                url = btn['url']
                if '?start=' in url:
                    raw_btn = url.split('?start=')[1]
                    text += parse_button(raw_btn, name)
                else:
                    text += f"\n[{btn['text']}](btnurl:{btn['url']}*!repl!*)"
            elif 'callback_data' in btn:
                text += parse_button(btn['callback_data'], name)

            if btn_num > 1:
                text = text.replace('*!repl!*', ':same')
            else:
                text = text.replace('*!repl!*', '')
    return text


async def get_msg_file(message: Message) -> Optional[dict]:
    # TODO: Remove file type or something
    message_id = message.message_id

    tmsg = await tbot.get_messages(message.chat.id, ids=message_id)

    file_types = ['sticker', 'photo', 'document', 'video', 'audio', 'video_note', 'voice']
    for file_type in file_types:
        if file_type not in message:
            continue
        return {'id': tmsg.file.id, 'type': file_type}
    return None


async def get_parsed_note_list(message: Message, allow_reply_message=True, split_args=1) -> BaseNote:
    # Default params
    preview = False
    file = None

    # IDK what this do OwO
    if not (to_split := ''.join([" " + q for q in get_args(message)[:split_args]])):
        to_split = ' '

    if "reply_to_message" in message and allow_reply_message:
        # Get parsed reply msg text
        parse_mode = get_msg_parse(message.reply_to_message.text)
        text = get_parsed_msg(message.reply_to_message, parse_mode)

        # Get parsed origin msg text
        if origin_raw_text := get_message_raw_text(message).partition(message.get_command() + to_split)[2][1:]:
            text += '\n'  # A delimeter between replied and origin messages
            text += get_parsed_msg(message, parse_mode)
            # Set parse_mode if origin msg override it
            if mode := get_msg_parse(origin_raw_text, default=None):
                parse_mode = mode

        # Get message keyboard
        if 'reply_markup' in message.reply_to_message and 'inline_keyboard' in message.reply_to_message.reply_markup:
            text += get_reply_msg_buttons_text(message.reply_to_message)

        # Check on attachment
        if msg_file := await get_msg_file(message.reply_to_message):
            file = msg_file
    else:
        parse_mode = get_msg_parse(get_message_raw_text(message))
        text = get_parsed_msg(message, parse_mode)
        if message.get_command() and message.get_args():
            text = text.partition(message.get_command() + to_split)[2][1:]
        # Check on attachment
        if msg_file := await get_msg_file(message):
            file = msg_file

    # Preview
    if '%PREVIEW' in text:
        text = text.replace('%PREVIEW', '')
        preview = True

    return BaseNote(
        parse_mode=parse_mode,
        file=file,
        text=text,
        preview=preview
    )


async def unparse_note_item(message: Message, note: BaseNote, chat_id: ChatId, 
                            raw=None, event=None, user=None) -> Tuple[str, dict]:
    """Unparses BaseNote and prepares args for send_message method"""
    text = note.text or ''
    file_id = None
    markup = None

    if note.file:
        file_id = note.file.id

    # Text processing
    if len(text) > 4090:
        text = text[:4087] + '...'

    if raw:
        markup = None
        if not note.parse_mode:
            text += '\n%PARSEMODE_NONE'
        elif note.parse_mode == 'html':
            text += '\n%PARSEMODE_HTML'

        if note.preview:
            text += '\n%PREVIEW'

    else:
        pm = message.chat.type == 'private'

        if text:
            text, markup = button_parser(chat_id, text, pm=pm)
            text = await vars_parser(
                text,
                message,
                md=True if note.parse_mode == 'md' else False,
                event=event,
                user=user or message.from_user
            )
            text = random_parser(text)

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

    except Exception as err:
        log.error("Something happened on sending note", exc_info=err)


def button_parser(chat_id: ChatId, texts: str, pm=False) -> Tuple[str, Optional[List[Button]]]:
    # buttons = InlineKeyboardMarkup(row_width=row_width)
    buttons: List[Button] = []
    raw_buttons = BUTTONS_REGEXP.findall(texts)
    text = BUTTONS_REGEXP.sub('', texts)

    btn = None
    for raw_button in raw_buttons:
        name = raw_button[0]
        action = raw_button[1] if raw_button[1] not in ('button', 'btn') else raw_button[2]

        if raw_button[3]:
            argument = raw_button[3][1:].lower().replace('`', '')
        elif action == '#':
            argument = raw_button[2]
        else:
            argument = ''

        if action in BUTTONS.keys():
            cb = BUTTONS[action]
            string = f'{cb}_{argument}_{chat_id}' if argument else f'{cb}_{chat_id}'
            # start_btn = InlineKeyboardButton(name, url=START_URL + string)
            # cb_btn = InlineKeyboardButton(name, callback_data=string)
            start_btn = Button.url(name, START_URL + string)
            cb_btn = Button.inline(name, string)

            if cb.endswith('sm'):
                btn = cb_btn if pm else start_btn
            elif cb.endswith('cb'):
                btn = cb_btn
            elif cb.endswith('start'):
                btn = start_btn
            elif cb.startswith('url'):
                # Workaround to make URLs case-sensitive TODO: make better
                argument = raw_button[3][1:].replace('`', '') if raw_button[3] else ''
                btn = Button.url(name, argument)
            elif cb.endswith('rules'):
                btn = start_btn
        elif action == 'url':
            argument = raw_button[3][1:].replace('`', '') if raw_button[3] else ''
            if argument[0] == '/' and argument[1] == '/':
                argument = argument[2:]
            # btn = InlineKeyboardButton(name, url=argument) 
            btn = Button.url(name, argument)
        else:
            # If btn not registred
            btn = None
            if argument:
                text += f'\n[{name}].(btn{action}:{argument})'
            else:
                text += f'\n[{name}].(btn{action})'
                continue

        if btn:
            # buttons.insert(btn) if raw_button[4] else buttons.add(btn)
            if len(buttons) < 1 and raw_button[4]:
                # buttons.add(btn)
                buttons.append([btn])
            else:
                buttons[-1].append(btn) if raw_button[4] else buttons.append([btn])

    return text, buttons or None  # None not needed for aiogram


async def vars_parser(text: str, message: Message, md=False, event: Message = None, user=None) -> str:
    if event is None:
        event = message

    if not text:
        return text

    first_name = html.escape(user.first_name, quote=False)
    last_name = html.escape(user.last_name or "", quote=False)
    user_id = ([user.id for user in event.new_chat_members][0]
               if 'new_chat_members' in event and event.new_chat_members != [] else user.id)
    mention = await get_user_link(user_id, md=md)

    if hasattr(event, 'new_chat_members') and event.new_chat_members and event.new_chat_members[0].username:
        username = "@" + event.new_chat_members[0].username
    elif user.username:
        username = "@" + user.username
    else:
        username = mention

    chat_id = message.chat.id
    chat_name = html.escape(message.chat.title or 'Local', quote=False)

    return text.replace('{first}', first_name) \
        .replace('{last}', last_name) \
        .replace('{fullname}', first_name + " " + last_name) \
        .replace('{id}', str(user_id).replace('{userid}', str(user_id))) \
        .replace('{mention}', mention) \
        .replace('{username}', username) \
        .replace('{chatid}', str(chat_id)) \
        .replace('{chatname}', str(chat_name)) \
        .replace('{chatnick}', str(message.chat.username or chat_name))


def random_parser(text: str) -> str:
    for item in RANDOM_REGEXP.finditer(text):
        random_item = choice(item.group(1).split('|'))
        text = text.replace(item.group(0), str(random_item))
    return text

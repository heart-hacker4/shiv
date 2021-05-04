import re
from typing import Optional, List, Dict, Tuple

from aiogram.types import Message
from telethon.tl.custom import Button

from sophie_bot import BOT_USERNAME
from sophie_bot.types.chat import ChatId

BUTTONS: Dict[str, str] = {}
START_URL = f'https://t.me/{BOT_USERNAME}?start='
BUTTONS_REGEXP = re.compile(r'\[(.+?)]\((button|btn)?(.+?)(:.+?|)(:same|)\)(\n|)')


def parse_button(data, name: str) -> str:
    raw_button = data.split('_')
    raw_btn_type = raw_button[0]

    pattern = re.match(r'btn(.+)(sm|cb|start)', raw_btn_type)
    if not pattern:
        return ''

    action = pattern.group(1)
    args = raw_button[1]

    if action in BUTTONS:
        text = f"\n[{name}]({action}:{args}*!repl!*)"
    else:
        if args:
            text = f'\n[{name}]!({action}:{args})'
        else:
            text = f'\n[{name}]!({action})'

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


def button_parser(chat_id: ChatId, texts: str, pm=False) -> Tuple[str, Optional[List[Button]]]:
    # buttons = InlineKeyboardMarkup(row_width=row_width)
    buttons: List[Button] = []
    raw_buttons = BUTTONS_REGEXP.findall(texts)
    text = BUTTONS_REGEXP.sub('', texts)

    btn = None
    for raw_button in raw_buttons:
        name = raw_button[0]
        action = raw_button[2]

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

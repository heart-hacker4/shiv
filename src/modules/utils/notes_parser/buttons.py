import re
from enum import Enum, auto
from typing import AnyStr, List, Match, NamedTuple, Optional

from aiogram.types import Message
from aiogram.types.inline_keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from odmantic import EmbeddedModel
from telethon.tl.custom import Button as TButton

from src import BOT
from src.types.chat import ChatId
from .random_parse import random_parser

START_URL = f'https://t.me/{BOT.username}?start='
BUTTONS_TEXT_REGEXP = re.compile(
    # [Button name](type:argument:same)
    r'\[(.+?)]\((?:button|btn)?(?!http(?:s))(\w+|#)(?:(?:[:=])?(?:\s)?(?://)?(.*?)|)[:=]?(?:(?:\s)?(same|\^))?\)(?:\n)?'
)
BUTTON_CALLBACK_PATTERN = "{prefix}-{action}-{argument}-{chat_id}"
BUTTONS_CALLBACK_REGEXP = re.compile(
    r'(.*?)-(.*?)-(.*?)-(.*)'
)


class DefinedButtonType(Enum):
    smart = auto()
    callback = auto()
    start = auto()
    url = auto()


class RealButtonTypes(Enum):
    url = auto()
    callback = auto()


class DBButton(EmbeddedModel):
    name: str
    action: str
    argument: str


class DefinedButtonOptions(NamedTuple):
    cb_prefix: str
    type: DefinedButtonType
    argument_optional: bool


BUTTONS = {
    'url': DefinedButtonOptions('', type=DefinedButtonType.url, argument_optional=False)
}


class ButtonException(Exception):
    pass


class WrongButtonAction(ButtonException):
    def __init__(self, button_name, action):
        self.button_name = button_name
        self.action = action


class ButtonShouldHaveArgument(ButtonException):
    def __init__(self, button_name, action):
        self.button_name = button_name
        self.action = action


class TooMuchButtonsInRow(ButtonException):
    pass


BUTTONS_EXCEPTIONS = (
    WrongButtonAction,
    ButtonShouldHaveArgument,
    TooMuchButtonsInRow
)


class ButtonFabric(List[List[DBButton]]):
    """Represents a inline buttons of a message. Can be stored in the database.
    Contains a functions to parse and unparse buttons."""

    @staticmethod
    def test_button_before_saving(button_name: str, action, argument):
        """Raises a exception if button has a problem."""
        if action not in BUTTONS:
            raise WrongButtonAction(button_name=button_name, action=action)

        defined_button_options: DefinedButtonOptions = BUTTONS[action]
        if not defined_button_options.argument_optional and not argument:
            raise ButtonShouldHaveArgument(button_name=button_name, action=action)

    def parse_text(self, text: str) -> str:
        """Parses a text into buttons. Returns a text without buttons."""
        raw_buttons: List[Match[AnyStr]] = BUTTONS_TEXT_REGEXP.findall(text)
        for raw_button in raw_buttons:
            button_name: str = raw_button[0]
            action: str = raw_button[1]
            argument: str = raw_button[2]
            same_row: bool = bool(raw_button[3])

            self.test_button_before_saving(button_name, action, argument)
            self.add_button(button_name, action, argument, same_row=same_row)

        return BUTTONS_TEXT_REGEXP.sub('', text)

    def parse_message(self, message: Message) -> bool:
        """Parses a message with buttons. Returns if buttons are found"""
        if not message.reply_markup or not message.reply_markup.inline_keyboard:
            # There is no inline buttons in message
            return False

        for row in message.reply_markup.inline_keyboard:
            for idx, button in enumerate(row):
                button_name: str = button['text']
                same_row: bool = idx > 0

                if button.callback_data or button.url and button.url.startswith(START_URL):
                    string: str = button['url'].split(START_URL)[1] if 'url' in button else button['callback_data']

                    if not (data := BUTTONS_CALLBACK_REGEXP.search(string)):
                        # A button from older SophieBot syntax or other bots, let's skip it.
                        continue

                    data: Match[AnyStr]
                    action = data[2]
                    argument = data[3]
                elif button.url:
                    # A simple url button
                    action = 'url'
                    argument = button['url']
                else:
                    # A wrong button type, let's skip it
                    continue

                self.test_button_before_saving(button_name, action, argument)
                self.add_button(button_name, action, argument, same_row=same_row)

        return True

    def add_button(
            self,
            button_name: str,
            action: str,
            argument: Optional[str],
            same_row: bool = False
    ):
        # Name url https://google.com
        # Name smart test_cb
        button = DBButton(name=button_name, action=action, argument=argument)

        if not same_row or len(self) < 1:
            self.append([button])
        else:
            self[-1].append(button)

    @staticmethod
    def get_smart_button(button: DBButton, argument: Optional[str] = None):
        url: str = START_URL + argument or button['argument']
        return button['name'], RealButtonTypes.url, url

    @staticmethod
    def get_callback_button(button: DBButton, argument: Optional[str] = None):
        return button['name'], RealButtonTypes.callback, argument or button['argument']

    def get_callback(self, button: DBButton, options: DefinedButtonOptions, chat_id: ChatId):
        return BUTTON_CALLBACK_PATTERN.format(
            prefix=options.cb_prefix,
            action=button['action'],
            argument=button['argument'],
            chat_id=chat_id
        )

    def unparse_button(self, button: dict, is_pm: bool, chat_id: ChatId) -> (str, RealButtonTypes, str):
        options = BUTTONS[button['action']]
        callback_data = self.get_callback(button, options, chat_id)

        if options.type is DefinedButtonType.url:
            return button['name'], RealButtonTypes.url, button['argument']

        elif options.type is DefinedButtonType.callback:
            return self.get_callback_button(button)

        # Here is buttons a little more complicated
        elif options.type is DefinedButtonType.start:
            return self.get_smart_button(button, argument=callback_data)

        elif options.type is DefinedButtonType.smart:
            if is_pm:
                return self.get_callback_button(button, argument=callback_data)
            else:
                return self.get_smart_button(button, argument=callback_data)

    def unparse_to_text(self) -> str:
        """Unparses buttons to text. Uses the most modern buttons syntax."""
        result = ''

        for row in self:
            for idx, button in enumerate(row):
                text = f"[{button['name']}]({button['action']}"
                if button['argument']:
                    text += f":{button['argument']}"
                if idx != 0:
                    # Same row
                    text += ':^'
                text += ')\n'
                result += text

        return result

    @staticmethod
    def apply_random_name(button_name: str) -> str:
        return random_parser(button_name)

    def aiogram(self, chat_id: ChatId, is_pm: bool = False) -> InlineKeyboardMarkup:
        """Unparses buttons for aiorgam send_message function"""
        markup = InlineKeyboardMarkup()

        for row in self:
            for idx, button in enumerate(row):
                button_name, button_type, argument = self.unparse_button(button, is_pm, chat_id)

                kwargs = {}
                if button_type is RealButtonTypes.url:
                    kwargs['url'] = argument
                elif button_type is RealButtonTypes.callback:
                    kwargs['callback_data'] = argument

                button = InlineKeyboardButton(self.apply_random_name(button_name), **kwargs)

                if idx > 0:
                    markup.insert(button)
                else:
                    markup.add(button)

        return markup

    def telethon(self, chat_id: ChatId, is_pm: bool = False) -> List[List[TButton]]:
        rows = []
        for row in self:
            for idx, button in enumerate(row):
                button_name, button_type, argument = self.unparse_button(button, is_pm, chat_id)

                if button_type is RealButtonTypes.url:
                    button = TButton.url(button_name, argument)
                elif button_type is RealButtonTypes.callback:
                    button = TButton.inline(button_name, argument)

                if not idx > 0 or len(self) < 1:
                    rows.append([button])
                else:
                    rows[-1].append(button)

        return rows

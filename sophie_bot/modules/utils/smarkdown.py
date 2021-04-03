# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
# Copyright (C) 2017 - 2020 Telethon

#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import warnings

from telethon.helpers import add_surrogate, del_surrogate, strip_text
from telethon.tl import TLObject
from telethon.tl.types import (
    MessageEntityBold, MessageEntityItalic, MessageEntityCode,
    MessageEntityPre, MessageEntityTextUrl, MessageEntityMentionName,
    MessageEntityStrike, MessageEntityUnderline
)
from aiogram.utils.text_decorations import TextDecoration


class SDecoration(TextDecoration):
    def link(self, value: str, link: str) -> str:
        return f"[{value}]({link})"

    def bold(self, value: str) -> str:
        return f'**{value}**'

    def italic(self, value: str) -> str:
        return f"__{value}__"

    def code(self, value: str) -> str:
        return f"`{value}`"

    def pre(self, value: str) -> str:
        return f'```{value}```'

    def pre_language(self, value: str, language: str) -> str:
        return f"```{language}\n{value}\n```"

    def underline(self, value: str) -> str:
        return f'++{value}++'

    def strikethrough(self, value: str) -> str:
        return f'~~{value}~~'

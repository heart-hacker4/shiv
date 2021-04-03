# Copyright (C) 2020 - 2021 MrYacha.
# Copyright (C) 2020 SitiSchu.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of Sophie.

from typing import Any


class SanTeXDoc:
    def __init__(self, *args):
        self.items = list(args)

    def __str__(self) -> str:
        return '\n'.join([str(items) for items in self.items])

    def add(self, other: Any):
        self.items.append(other)
        return self

    def __add__(self, other):
        return self.add(other)


class StyleFormationCore:
    start: str
    end: str

    def __init__(self, data: Any):
        self.text = f'{self.start}{str(data)}{self.end}'

    def __str__(self) -> str:
        return self.text


class Bold(StyleFormationCore):
    start = '<b>'
    end = '</b>'


class Italic(StyleFormationCore):
    start = '<i>'
    end = '</i>'


class Code(StyleFormationCore):
    start = '<code>'
    end = '</code>'


class Pre(StyleFormationCore):
    start = '<pre>'
    end = '</pre>'


class Strikethrough(StyleFormationCore):
    start = '<s>'
    end = '</s>'


class Underline(StyleFormationCore):
    start = '<u>'
    end = '</u>'


class Section:
    def __init__(self, *args, title: str = '', title_underline=True, title_bold=True, indent=2, postfix=':'):
        self.title_text = title
        self.items = list(args)
        self.indent = indent
        self.title_underline = title_underline
        self.title_bold = title_bold
        self.postfix = postfix

    @property
    def title(self) -> str:
        title = self.title_text
        text = str(Underline(title)) if self.title_underline else title
        if self.title_bold:
            text = str(Bold(text))
        text += self.postfix
        return text

    def __str__(self) -> str:
        text = ''
        text += self.title
        space = ' ' * self.indent
        for item in self.items:
            text += '\n'

            if type(item) == Section:
                item.indent *= 2
            if type(item) == VList:
                item.indent = self.indent
            if type(item) == Text:
                item.indent = self.indent
            else:
                text += space

            text += str(item)

        return text

    def add(self, other: Any):
        self.items.append(other)
        return self

    def __add__(self, other):
        return self.add(other)


class VList:
    def __init__(self, *args, indent=0, prefix='- '):
        self.items = list(args)
        self.prefix = prefix
        self.indent = indent

    def __str__(self) -> str:
        space = ' ' * self.indent if self.indent else ' '
        text = ''
        for idx, item in enumerate(self.items):
            if idx > 0:
                text += '\n'
            text += f'{space}{self.prefix}{item}'

        return text

    def add(self, other: Any):
        self.items.append(other)
        return self

    def __add__(self, other):
        return self.add(other)


class HList:
    def __init__(self, *args, prefix=''):
        self.items = list(args)
        self.prefix = prefix

    def __str__(self) -> str:
        text = ''
        for idx, item in enumerate(self.items):
            if idx > 0:
                text += ' '
            if self.prefix:
                text += self.prefix
            text += str(item)

        return text

    def add(self, other: Any):
        self.items.append(other)
        return self

    def __add__(self, other):
        return self.add(other)


class Text:
    def __init__(self, data: Any):
        self.data = data

    def __str__(self):
        return str(self.data)


class KeyValue:
    def __init__(self, title, value, suffix=': ', title_bold=True):
        self.title = Bold(title) if title_bold else title
        self.value = value
        self.suffix = suffix

    def __str__(self) -> str:
        return f'{self.title}{self.suffix}{self.value}'

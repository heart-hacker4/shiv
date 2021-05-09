from aiogram.utils.text_decorations import TextDecoration, HtmlDecoration


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


class HtmlDecorationWithoutEscaping(HtmlDecoration):
    def quote(self, value: str) -> str:
        return value

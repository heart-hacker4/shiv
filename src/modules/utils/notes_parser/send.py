from typing import Optional, Tuple

from aiogram.types import InputMedia, Message, MessageId, User

from src import bot
from src.models.notes import BaseNote, CAPTION_LENGTH, ParseMode
from src.services.tg_telethon import tbot
from src.types.chat import ChatId
from .buttons import BUTTONS_EXCEPTIONS, ButtonFabric
from .text import random_parser, vars_parser

MULTI_MESSAGE_FILE = ('sticker', 'video_note', 'contact')
FILE_TYPES_NO_PREVIEW = ['animation']
FILE_TYPES_FUNCS = {
    'photo': bot.send_photo,
    'sticker': bot.send_sticker,
    'audio': bot.send_audio,
    'video_note': bot.send_video_note,
    'voice': bot.send_voice,
    'animation': bot.send_animation,
    'document': bot.send_document,
    'contact': bot.send_contact
}


async def send_new_note(
        send_id: ChatId,
        note: BaseNote,
        reply_to: MessageId,
        raw: bool = False,
        message: Optional[Message] = None,
        user: Optional[User] = None,
        is_pm: bool = False
) -> Tuple[Message, ...]:
    """A modern and nice way to send notes"""

    # Parse mode
    if (parse_mode := note.parse_mode) is ParseMode.preformatted:
        parse_mode = ParseMode.html

    # Buttons
    buttons = ButtonFabric(note.buttons or [])

    # Text processing
    text = note.text or ''
    if not raw:
        text = random_parser(text)
        if message:
            text = vars_parser(
                text,
                message,
                user or message.from_user,
                no_parse=parse_mode is ParseMode.none
            )
        reply_markup = buttons.aiogram(send_id, is_pm=is_pm) if note.buttons else None
    else:
        text += '\n'  # add a divider newline
        text += buttons.unparse_to_text()
        reply_markup = None

    # Text processing
    if len(text) > 4090:
        text = text[:4087] + '...'

    media_group: bool = note.files and len(note.files) > 1
    # Decide if we should to add a caption here or send a different message
    if not raw and len(text) <= CAPTION_LENGTH and not buttons and (
            not note.files or not any([x.caption for x in note.files])):
        last_caption = True
    else:
        last_caption = False

    files_type: Optional[str] = note.files[0].type if note.files else None

    # Send a multi message
    multi_message: bool = text and note.files and files_type in MULTI_MESSAGE_FILE or media_group and not last_caption

    msgs: Tuple[Message, ...] = ()
    if files_type:
        kwargs = {
            'reply_to_message_id': reply_to
        }

        if not media_group:
            kwargs['reply_markup'] = reply_markup

        if files_type not in MULTI_MESSAGE_FILE and not media_group:
            kwargs['parse_mode'] = parse_mode.value
            kwargs['caption'] = text
            if files_type not in FILE_TYPES_NO_PREVIEW:
                kwargs['disable_web_page_preview'] = note.preview

        if media_group:
            # Send a media group

            group_list = []
            for idx, item in enumerate(note.files, start=1):
                caption = item.caption
                if last_caption:
                    caption = text if idx == len(note.files) else caption

                group_list.append(
                    InputMedia(type=item.type, media=item.id, parse_mode=parse_mode, caption=caption)
                )

            msgs = (await bot.send_media_group(
                send_id,
                group_list,
                **kwargs
            ))
        else:
            # Send a media
            msgs = (await FILE_TYPES_FUNCS[files_type](
                send_id,
                note.files[0].id,
                **kwargs
            ))

    if multi_message:
        # Unsets reply_to, as we already replied to a message with above media message
        reply_to = None

    # Send text message
    if not files_type or multi_message:
        return (*msgs, await bot.send_message(
            chat_id=send_id,
            text=text,
            parse_mode=parse_mode.value,
            reply_markup=reply_markup,
            reply_to_message_id=reply_to,
            disable_web_page_preview=not note.preview
        ))

    return msgs


async def send_old_note(
        note: BaseNote,
        send_id: ChatId,
        message: Optional[Message] = None,
        user: Optional[User] = None,
        is_pm: bool = False,
        raw: bool = False
) -> Message:
    """Sends note in "compatible" mode"""

    text = note.text or ''

    if note.files:
        # Not supports media groups
        file_id = note.files[0].id
    else:
        file_id = None

    # Text processing
    if len(text) > 4090:
        text = text[:4087] + '...'

    if raw:
        reply_markup = None
        if not note.parse_mode:
            text += '\n%PARSE:none'
        elif note.parse_mode == 'html':
            text += '\n%PARSE:html'
        if note.preview:
            text += '\n%PREVIEW'

    elif text:
        buttons = ButtonFabric(note.buttons or [])
        try:
            text = buttons.parse_text(text)
        except BUTTONS_EXCEPTIONS:
            return await bot.send_message(send_id, 'I found this note invalid! Please update it (read Wiki).')

        if message:
            text = vars_parser(
                text,
                message,
                user or message.from_user,
                md=True
            )

        reply_markup = buttons.telethon(send_id, is_pm=is_pm)

    elif not text and not file_id:
        text = '‎ㅤ‎'

    return await tbot.send_message(
        send_id,
        text,
        buttons=reply_markup,
        parse_mode=None if raw else note.parse_mode.value,
        file=file_id,
        link_preview=note.preview
    )


async def send_note(
        send_id: ChatId,
        note: BaseNote,
        reply_to: MessageId,
        raw: bool = False,
        message: Optional[Message] = None,
        user: Optional[User] = None,
        is_pm: bool = False
) -> Tuple[Message, ...]:
    """General send note method"""
    if note.old:
        return await send_old_note(note, send_id, message=message, user=user, is_pm=is_pm, raw=raw),

    return await send_new_note(
        send_id=send_id,
        note=note,
        reply_to=reply_to,
        raw=raw,
        message=message,
        user=user,
        is_pm=is_pm
    )

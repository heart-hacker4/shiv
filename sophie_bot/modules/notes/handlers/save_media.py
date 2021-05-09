import asyncio
from typing import List

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message, ContentType
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from bson import ObjectId

from sophie_bot.decorator import register
from sophie_bot.models.notes import NoteFile, CAPTION_LENGTH
from sophie_bot.modules.utils.connections import chat_connection
from sophie_bot.modules.utils.language import get_strings_dec
from sophie_bot.modules.utils.message import need_args_dec
from sophie_bot.modules.utils.notes_parser.encode import get_msg_file
from sophie_bot.modules.utils.notes_parser.encode import get_parsed_note_list
from sophie_bot.services.mongo import engine
from ..models import SavedNote
from ..utils.saving import get_note_description, get_names_group, upsert_note, build_saved_text

MEDIA_CONTENT_TYPES = [
    ContentType.PHOTO,
    ContentType.AUDIO,
    ContentType.DOCUMENT,
    ContentType.VIDEO
]


class SaveNoteMedia(StatesGroup):
    work = State()


note_media_done = CallbackData('note_media_done_cb', 'note_id')
SAVE_MEDIA_GROUP_LOCK = asyncio.Lock()


@register(cmds=['savemedia', 'savegallery', 'setmedia', 'setgallery'], user_admin=True, allow_kwargs=True)
@need_args_dec()
@chat_connection(admin=True)
@get_strings_dec('notes')
async def save_note_gallery(message: Message, chat: dict, strings: dict, state=None, **kwargs) -> Message:
    chat_id = chat['chat_id']

    if type(data := await get_names_group(strings, message, chat_id)) is Message:
        # Returned a error message, skip everything
        return data
    note_names, note_group = data
    note_data = await get_parsed_note_list(message, skip_files=True)

    # Note description
    desc, note_data.text = get_note_description(note_data.text)

    # Let's save a blank note, without a files, just text
    note, status = await upsert_note(
        chat_id,
        desc,
        note_names,
        message.from_user.id,
        note_data,
        note_group
    )
    # Enter a state to save files
    await SaveNoteMedia.work.set()
    async with state.proxy() as proxy:
        proxy['id'] = str(note.id)

    buttons = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            strings['done_button'],
            callback_data=note_media_done.new(note_id=str(note.id))
        ),
        InlineKeyboardButton(
            strings['cancel_button'],
            callback_data='cancel'
        )
    )

    return await message.reply(
        '\n'.join(map(lambda c: strings[c], ['send_files', 'send_files_1', 'send_files_2'])),
        reply_markup=buttons
    )


@register(state=SaveNoteMedia.work, content_types=MEDIA_CONTENT_TYPES, allow_edited=False, allow_kwargs=True)
@get_strings_dec('notes')
async def save_file_group_worker(message: Message, strings: dict, state=None, **kwargs):
    file = get_msg_file(message)

    async with state.proxy() as proxy:
        files: List[dict] = proxy.get('files', [])

        if proxy.get('file_type', file['type']) != file['type']:
            return await message.reply('\n'.join(map(lambda c: strings[c], ['bad_file_type', 'bad_file_type_1'])))
        proxy['file_type'] = file['type']

        if len(files) >= 10:
            await state.finish()
            return await message.reply(strings['too_much_files'])

    file_data = NoteFile(**file)

    # Append a new file id
    async with SAVE_MEDIA_GROUP_LOCK:
        async with state.proxy() as proxy:
            if 'files' not in proxy:
                proxy['files'] = []
            proxy['files'].append(file_data.dict())


@register(state=SaveNoteMedia.work, content_types=ContentType.TEXT, allow_kwargs=True)
@get_strings_dec('notes')
async def save_caption_worker(message: Message, strings: dict, state=None, **kwargs):
    """Adds/updates a caption of last file by a simple text message"""
    async with state.proxy() as proxy:
        files: List[dict] = proxy.get('files', [])

        # A file caption message
        if len(files) == 0 and message.content_type is ContentType.TEXT:
            return await message.reply(strings['no_file_for_caption'])
        elif message.content_type is ContentType.TEXT:
            # Update a previous saved file caption

            if len(new_caption := message.text) > CAPTION_LENGTH:
                return await message.reply(strings['caption_too_big'].format(CAPTION_LENGTH))

        files[-1]['caption'] = new_caption


@register(note_media_done.filter(), state=SaveNoteMedia.work, f='cb', is_admin=True, allow_kwargs=True)
@chat_connection(admin=True)
@get_strings_dec('notes')
async def clear_all_notes_cb(event, chat, strings, state=None, callback_data=None, **kwargs):
    async with state.proxy() as proxy:
        files: List[str] = proxy['files']
        file_type: str = proxy['file_type']

    await state.finish()

    if not (saved_note := await engine.find_one(
            SavedNote, (SavedNote.chat_id == chat['chat_id']) & (SavedNote.id == ObjectId(callback_data['note_id']))
    )):
        return

    saved_note.note.files = [NoteFile(**x) for x in files]
    await engine.save(saved_note)

    doc = build_saved_text(
        strings=strings,
        chat_name=chat['chat_title'],
        description=saved_note.description,
        note_names=saved_note.names,
        note=saved_note.note,
        note_group=saved_note.group
    )

    await event.message.edit_text(str(doc))

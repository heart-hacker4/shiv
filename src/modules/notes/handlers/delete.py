from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from src.decorator import register
from src.modules.utils.connections import chat_connection
from src.modules.utils.language import get_strings_dec
from src.modules.utils.message import get_arg, need_args_dec, get_args
from src.services.mongo import db, engine
from ..models import SavedNote
from ..utils.get import get_similar_note


@register(cmds=['clear', 'delnote'])
@chat_connection(admin=True)
@need_args_dec()
@get_strings_dec('notes')
async def clear_multiple_notes(message, chat, strings):
    # TODO: decorator
    args = get_args(message)
    if len(args) < 2 and '|' not in ''.join(args):
        return

    removed = ''
    not_removed = ''
    for note_name in note_names:
        if note_name[0] == '#':
            note_name = note_name[1:]

        if not (note := await db.notes.find_one({'chat_id': chat['chat_id'], 'names': {'$in': [note_name]}})):
            if len(note_names) <= 1:
                text = strings['cant_find_note'].format(chat_name=chat['chat_title'])
                if alleged_note_name := await get_similar_note(chat['chat_id'], note_name):
                    text += strings['u_mean'].format(note_name=alleged_note_name)
                await message.reply(text)
                return
            else:
                not_removed += ' #' + note_name
                continue

        await db.notes.delete_one({'_id': note['_id']})
        removed += ' #' + note_name

    if len(note_names) > 1:
        text = strings['note_removed_multiple'].format(chat_name=chat['chat_title'], removed=removed)
        if not_removed:
            text += strings['not_removed_multiple'].format(not_removed=not_removed)
        await message.reply(text)
    else:
        await message.reply(strings['note_removed'].format(note_name=note_name, chat_name=chat['chat_title']))


@register(cmds=['clear', 'delnote'])
@chat_connection(admin=True)
@need_args_dec()
@get_strings_dec('notes')
async def clear_note(message, chat, strings):
    chat_id = chat['chat_id']
    note_name = get_arg(message).lower().removeprefix('#')

    if not (
            note := await engine.find_one(SavedNote,
                                          (SavedNote.chat_id == chat_id) & (SavedNote.names.in_([note_name])))):
        text = strings['cant_find_note'].format(chat_name=chat['chat_title'])
        if alleged_note_name := await get_similar_note(chat['chat_id'], note_name):
            text += strings['u_mean'].format(note_name=alleged_note_name)
        return await message.reply(text)

    await engine.delete(note)
    await message.reply(strings['note_removed'].format(note_name=note_name, chat_name=chat['chat_title']))


@register(cmds='clearall')
@chat_connection(admin=True)
@get_strings_dec('notes')
async def clear_all_notes(message, chat, strings):
    # Ensure notes count
    if not await db.notes.find_one({'chat_id': chat['chat_id']}):
        await message.reply(strings['notelist_no_notes'].format(chat_title=chat['chat_title']))
        return

    text = strings['clear_all_text'].format(chat_name=chat['chat_title'])
    buttons = InlineKeyboardMarkup()
    buttons.add(InlineKeyboardButton(strings['clearall_btn_yes'], callback_data='clean_all_notes_cb'))
    buttons.add(InlineKeyboardButton(strings['clearall_btn_no'], callback_data='cancel'))
    await message.reply(text, reply_markup=buttons)


@register(regexp='clean_all_notes_cb', f='cb', is_admin=True)
@chat_connection(admin=True)
@get_strings_dec('notes')
async def clear_all_notes_cb(event, chat, strings):
    num = (await db.notes.delete_many({'chat_id': chat['chat_id']})).deleted_count

    text = strings['clearall_done'].format(num=num, chat_name=chat['chat_title'])
    await event.message.edit_text(text)

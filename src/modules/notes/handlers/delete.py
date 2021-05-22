from aiogram.types.inline_keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from stfu_tg import Doc, HList, Section, VList

from src import dp
from src.modules.utils.connections import chat_connection
from src.modules.utils.language import get_strings_dec
from src.modules.utils.message import get_arg, need_args_dec
from ..db.notes import del_all_notes, del_note, get_note, get_notes
from ..utils.get import get_note_name, get_similar_note


@dp.message_handler(commands=['clear', 'delnote'], text_contains='|', is_admin=True)
@chat_connection(admin=True)
@need_args_dec()
@get_strings_dec('notes')
async def clear_multiple_notes(message, chat, strings):
    # TODO: add a filter for many arguments
    notes_to_delete = get_arg(message).lower().split('|')

    deleted = []
    not_deleted = []

    for raw_note_name in notes_to_delete:
        note_name = get_note_name(raw_note_name)

        if not (note := await get_note(note_name, chat['chat_id'])):
            not_deleted.append(note_name)
            continue

        await del_note(note)
        deleted.append(note)

    sec = Section(title=strings['note_removed_multiple_title'].format(chat_name=chat['chat_title']))

    if deleted:
        sec += Section(
            VList(*[HList(*x.names, prefix='#') for x in deleted]), title=strings['note_removed_multiple_removed'],
            title_underline=False
        )
    if not_deleted:
        sec += Section(
            VList(*[f'#{x}' for x in not_deleted]), title=strings['note_removed_multiple_not_removed'],
            title_underline=False
        )

    if not deleted and not not_deleted:
        return await message.reply(strings['notes_wasnt_touched'])

    await message.reply(str(Doc(sec)))


@dp.message_handler(commands=['clear', 'delnote'], is_admin=True)
@chat_connection(admin=True)
@need_args_dec()
@get_strings_dec('notes')
async def clear_note(message, chat, strings):
    chat_id = chat['chat_id']
    note_name = get_arg(message).lower().removeprefix('#')

    if not (note := await get_note(note_name, chat_id)):
        text = strings['cant_find_note'].format(chat_name=chat['chat_title'])
        if alleged_note_name := await get_similar_note(chat['chat_id'], note_name):
            text += strings['u_mean'].format(note_name=alleged_note_name)
        return await message.reply(text)

    await del_note(note)
    await message.reply(strings['note_removed'].format(note_name=note_name, chat_name=chat['chat_title']))


@dp.message_handler(commands='clearall', is_admin=True)
@chat_connection(admin=True)
@get_strings_dec('notes')
async def clear_all_notes(message, chat, strings):
    # Ensure notes count
    if not await get_notes(chat['chat_id']):
        await message.reply(strings['notelist_no_notes'].format(chat_title=chat['chat_title']))
        return

    text = strings['clear_all_text'].format(chat_name=chat['chat_title'])
    buttons = InlineKeyboardMarkup()
    buttons.add(InlineKeyboardButton(strings['clearall_btn_yes'], callback_data='clean_all_notes_cb'))
    buttons.add(InlineKeyboardButton(strings['clearall_btn_no'], callback_data='cancel'))
    await message.reply(text, reply_markup=buttons)


@dp.callback_query_handler(text='clean_all_notes_cb', is_admin=True)
@chat_connection(admin=True)
@get_strings_dec('notes')
async def clear_all_notes_cb(event, chat, strings):
    num = (await del_all_notes(chat['chat_id'])).deleted_count

    text = strings['clearall_done'].format(num=num, chat_name=chat['chat_title'])
    await event.message.edit_text(text)

from datetime import datetime

from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from sophie_bot.decorator import register
from sophie_bot.modules.utils.connections import chat_connection
from sophie_bot.modules.utils.language import get_strings_dec
from sophie_bot.modules.utils.message import get_arg, need_args_dec, get_args
from sophie_bot.modules.utils.notes_parser.encode import get_parsed_note_list
from sophie_bot.modules.utils.text import STFDoc, Section, KeyValue, HList, Code
from sophie_bot.services.mongo import db, engine
from ..models import SavedNote, MAX_NOTES_PER_CHAT, MAX_GROUPS_PER_CHAT
from ..utils.get import get_similar_note
from ..utils.saving import check_note_names, check_note_group, get_notes_count, get_groups_count, get_note_description


@register(cmds=['save', 'setnote', 'savenote'], user_admin=True)
@need_args_dec()
@chat_connection(admin=True)
@get_strings_dec('notes')
async def save_note(message, chat, strings):
    chat_id = chat['chat_id']

    # Get note names
    arg = get_arg(message).lower()

    # Get note group
    if '^' in arg:
        arg = arg.replace((raw := arg.split('^', 1))[1], '')[:-1]
        if sym := check_note_group(note_group := raw[1]):
            return await message.reply(strings['group_cant_contain'].format(symbol=sym))

        if await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.names.in_([note_group]))):
            return await message.reply(strings['group_name_collision'].format(name=note_group))
    else:
        note_group = None

    note_names = [x.removeprefix('#') for x in arg.split('|')]
    if sym := check_note_names(note_names):
        return await message.reply(strings['notename_cant_contain'].format(symbol=sym))

    # Notes limit
    if await get_notes_count(chat_id) > MAX_NOTES_PER_CHAT:
        return await message.reply(strings['saved_too_much'])
    # Groups limit
    if await get_groups_count(chat_id) > MAX_GROUPS_PER_CHAT:
        return await message.reply(strings['saved_too_much'])

    if await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.group.in_(note_names))):
        return await message.reply(strings['note_name_collision'].format(name=note_group))

    note_data = await get_parsed_note_list(message)
    if not note_data.text and not note_data.file:
        await message.reply(strings['blank_note'])
        return

    # Note description
    desc, note_data.text = get_note_description(note_data.text)

    if note := await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.names.in_(note_names))):
        # status = 'updated'
        note.names = note_names
        note.description = desc
        note.edited_date = datetime.now()
        note.edited_user = message.from_user.id
        note.note = note_data
        note.group = note_group
    else:
        # status = 'saved'
        note = SavedNote(
            names=note_names,
            description=desc,
            chat_id=chat_id,
            created_date=datetime.now(),
            created_user=message.from_user.id,
            note=note_data,
            group=note_group
        )

    await engine.save(note)

    # Build reply text
    doc = STFDoc()
    sec = Section(
        # KeyValue(strings['status'], strings[status]),
        KeyValue(strings['names'], HList(*note_names, prefix='#')),
        KeyValue(strings['note_info_desc'], note.description),
        KeyValue(strings['note_info_parsing'], Code(str(strings[note.note.parse_mode]))),
        KeyValue(strings['note_info_preview'], note.note.preview),  # TODO: translateable
        title=strings['saving_title'].format(chat_name=chat['chat_title'])
    )

    if note_group:
        note_group = note_group
        sec += KeyValue(strings['note_group'], f'#{note_group}')

    doc += sec
    doc += Section(strings['you_can_get_notes'], title=strings['getting_tip'])

    await message.reply(str(doc))


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
    note := await engine.find_one(SavedNote, (SavedNote.chat_id == chat_id) & (SavedNote.names.in_([note_name])))):
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

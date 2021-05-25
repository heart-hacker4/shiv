# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
# Copyright (C) 2020 Jeepeo

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

from contextlib import suppress
from datetime import datetime, timedelta

from aiogram.utils.exceptions import MessageNotModified
from pymongo import UpdateOne
from stfu_tg import Code, KeyValue

from src.modules.notes.db.notes import count_of_filters
from src.modules.notes.models import CleanNotes, ExportModel, MAX_NOTES_PER_CHAT, PrivateNotes, SavedNote
from src.modules.notes.utils.get import get_note
from src.modules.notes.utils.saving import get_notes_count
from src.modules.utils.language import get_string
from src.services.mongo import db, engine

__data_model__ = ExportModel


async def __usage_count__():
    return KeyValue('Total notes', Code(await count_of_filters({})))


async def __detailed_stats__() -> tuple:
    last_48h_id = {'$gt': datetime.now() - timedelta(days=2)}

    return (
        KeyValue('Total notes', Code(await count_of_filters({}))),
        KeyValue('Old notes (compatibility mode)', Code(await count_of_filters({+SavedNote.note.old: True}))),
        KeyValue('New notes', Code(await count_of_filters({+SavedNote.note.old: False}))),
        KeyValue('Notes created in the last 48 hours',
                 Code(await count_of_filters({+SavedNote.created_date: last_48h_id}))),
        KeyValue('Notes edited in the last 48 hours',
                 Code(await count_of_filters({+SavedNote.edited_date: last_48h_id}))),
    )


async def __export_data__(chat_id) -> ExportModel:
    return ExportModel(
        notes=await engine.find(SavedNote, SavedNote.chat_id == chat_id),
        private_notes=bool(await engine.find_one(PrivateNotes, PrivateNotes.chat_id == chat_id)),
        clean_notes=bool(await engine.find_one(CleanNotes, CleanNotes.chat_id == chat_id))
    )


async def __import_data__(chat_id: int, data: ExportModel, overwrite=False):
    if overwrite:
        async for note in engine.find(SavedNote, SavedNote.chat_id == chat_id):
            await engine.delete(note)

        count_notes = 0
    else:
        count_notes = await get_notes_count(chat_id)

    # Notes limit
    if count_notes + len(data.notes) > MAX_NOTES_PER_CHAT:
        pass
    # TODO: groups limit

    batch_actions = []
    for note in data.notes:
        batch_actions.append(UpdateOne(
            # type: ignore
            (SavedNote.chat_id == chat_id) & (SavedNote.names.in_(note.names)),
            {
                # We don't want to allow to update note's chat_id and its id
                '$set': {
                    +SavedNote.chat_id: chat_id, **note.dict(
                        exclude={'chat_id', 'id', 'created_date', 'created_user'})
                },
                # Update created fields only on insert
                '$setOnInsert': {**note.dict(include={'created_date', 'created_user'})}
            },
            upsert=True
        ))

    await engine.get_collection(SavedNote).bulk_write(batch_actions)


async def filter_handle(message, chat, data):
    chat_id = chat['chat_id']
    read_chat_id = message.chat.id
    note_name = data['note_name']
    note = await db.notes.find_one({'chat_id': chat_id, 'names': {'$in': [note_name]}})
    await get_note(message, db_item=note, chat_id=chat_id, send_id=read_chat_id, reply_to=None)


async def setup_start(message):
    text = await get_string(message.chat.id, 'notes', 'filters_setup_start')
    with suppress(MessageNotModified):
        await message.edit_text(text)


async def setup_finish(message, data):
    note_name = message.text.split(' ', 1)[0].split()[0]

    if not (await db.notes.find_one({'chat_id': data['chat_id'], 'names': note_name})):
        await message.reply('no such note!')
        return

    return {'note_name': note_name}


__filters__ = {
    'get_note': {
        'title': {'module': 'notes', 'string': 'filters_title'},
        'handle': filter_handle,
        'setup': {
            'start': setup_start,
            'finish': setup_finish
        },
        'del_btn_name': lambda msg, data: f"Get note: {data['note_name']}"
    }
}

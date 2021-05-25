# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram

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

import asyncio
import io
from datetime import datetime, timedelta

import ujson
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.input_file import InputFile
from babel.dates import format_timedelta
from odmantic.engine import ModelType
from pydantic.error_wrappers import ValidationError
from stfu_tg import Code, Doc, KeyValue, Section, VList

from src import BOT_ID, SOPHIE_VERSION, bot
from src.models.imports_exports import ExportInfo, ExportModel, GeneralData
from src.modules import MODULES
from src.modules.utils.message import get_arg
from src.modules.utils.old_register import register
from src.services.redis import redis
from .utils.connections import chat_connection
from .utils.language import get_strings_dec

VERSION = 6


# Waiting for import file state
class ImportFileWait(StatesGroup):
    waiting = State()


@register(cmds='export', user_admin=True)
@chat_connection(admin=True)
@get_strings_dec('imports_exports')
async def export_chat_data(message, chat, strings):
    chat_id = chat['chat_id']
    key = 'export_lock:' + str(chat_id)
    if redis.get(key):
        ttl = format_timedelta(timedelta(seconds=redis.ttl(key)), strings['language_info']['babel'])
        await message.reply(strings['exports_locked'] % ttl)
        return

    redis.set(key, 1)
    redis.expire(key, 120)

    msg = await message.reply(strings['started_exporting'])
    modules = {}

    for module in [m for m in MODULES if hasattr(m, '__export_data__')]:
        await asyncio.sleep(0.2)

        module_name = module.__name__.split('.')[-1]
        module_data = await module.__export_data__(chat_id)
        if module_data:
            modules[module_name] = module_data.dict(exclude={'id'})

    data = ExportModel(
        export_info=ExportInfo(
            chat_name=chat['chat_title'],
            chat_id=chat_id,
            date=datetime.now(),
        ),
        general=GeneralData(
            sophie_version=SOPHIE_VERSION,
            sophie_id=BOT_ID,
            version=VERSION
        ), modules=modules
    )

    jfile = InputFile(io.StringIO(data.json(indent=2)), filename=f'{chat_id}_export.json')
    text = strings['export_done'].format(chat_name=chat['chat_title'])
    await message.answer_document(jfile, text, reply=message.message_id)
    await msg.delete()


@register(cmds='import', user_admin=True)
@get_strings_dec('imports_exports')
async def import_reply(message, strings):
    if 'document' in message:
        document = message.document
    else:
        if 'reply_to_message' not in message:
            await ImportFileWait.waiting.set()
            await message.reply(strings['send_import_file'])
            return

        elif 'document' not in message.reply_to_message:
            await message.reply(strings['rpl_to_file'])
            return
        document = message.reply_to_message.document

    await import_fun(message, document)


@register(state=ImportFileWait.waiting, content_types=types.ContentTypes.DOCUMENT, allow_kwargs=True)
async def import_state(message, state=None, **kwargs):
    await import_fun(message, message.document)
    await state.finish()


@chat_connection(admin=True, only_groups=True)
@get_strings_dec('imports_exports')
async def import_fun(message, document, chat, strings):
    chat_id = chat['chat_id']
    key = 'import_lock:' + str(chat_id)
    if redis.get(key):
        ttl = format_timedelta(timedelta(seconds=redis.ttl(key)), strings['language_info']['babel'])
        await message.reply(strings['imports_locked'] % ttl)
        return

    redis.set(key, 1)
    redis.expire(key, 7200)

    arg = get_arg(message)
    overwrite = False
    if arg in ('overwrite', 'replace'):
        overwrite = True

    msg = await message.reply(strings['started_importing'])
    if document['file_size'] > 52428800:
        await message.reply(strings['big_file'])
        return
    data = await bot.download_file_by_id(document.file_id, io.BytesIO())
    try:
        data = ujson.load(data)
    except ValueError:
        return await message.reply(strings['invalid_file'])

    if 'general' not in data:
        await message.reply(strings['bad_file'])
        return

    file_version = data['general']['version']

    if file_version > VERSION:
        await message.reply(strings['file_version_so_new'])
        return

    data_modules = data.get('modules', [])

    imported = []
    for module in [m for m in MODULES if hasattr(m, '__import_data__')]:
        module_name = module.__name__.replace('sophie_bot.modules.', '')
        if module_name not in data_modules:
            continue

        imported.append(module_name)
        await asyncio.sleep(0.2)

        try:
            module_data: ModelType = module.__data_model__(**data_modules[module_name])
            await module.__import_data__(chat_id, module_data, overwrite=overwrite)
        except ValidationError as validation_errors:
            error_list = []
            for error in validation_errors.errors():
                error_location = ('modules', module_name) + error['loc']
                error_list.append(KeyValue(' -> '.join(str(e) for e in error_location), Code(error['msg'])))

            return await message.reply(str(Doc(Section(
                KeyValue(strings['module_name'], module_name),
                Section(VList(*error_list), title=strings['error_msg']),
                title=strings['import_error_header']
            ))))

    text = strings['import_done'].format(chat_name=chat['chat_title'])
    text += '\n'
    text += strings['import_replace'] if overwrite else strings['import_append']
    await msg.edit_text(text)

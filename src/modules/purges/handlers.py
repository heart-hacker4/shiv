from asyncio import sleep

from src import bot, dp
from src.modules.utils.del_message import del_messages
from src.modules.utils.language import get_strings_dec


@dp.callback_query_handler(cmds="del", bot_can_delete_messages=True, user_can_delete_messages=True)
@get_strings_dec('msg_deleting')
async def del_message(message, strings):
    if not message.reply_to_message:
        await message.reply(strings['reply_to_msg'])
        return
    msgs = [message.message_id, message.reply_to_message.message_id]
    await del_messages(message.chat.id, msgs)


@dp.callback_query_handler(cmds="purge", no_args=True, bot_can_delete_messages=True, user_can_delete_messages=True)
@get_strings_dec('msg_deleting')
async def fast_purge(message, strings):
    if not message.reply_to_message:
        await message.reply(strings['reply_to_msg'])
        return
    msg_id = message.reply_to_message.message_id
    delete_to = message.message_id

    chat_id = message.chat.id
    msgs = []
    for m_id in range(int(delete_to), msg_id - 1, -1):
        msgs.append(m_id)
        if len(msgs) == 100:
            await del_messages(chat_id, msgs)

    if not await del_messages(chat_id, msgs):
        await message.reply(strings['purge_error'])
        return

    msg = await bot.send_message(chat_id, strings["fast_purge_done"])
    await sleep(5)
    await msg.delete()

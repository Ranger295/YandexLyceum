import os
import shutil
from time import sleep
import discord
from discord import SyncWebhook
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram import Bot, Dispatcher, executor, types
from asyncio import sleep
from time import sleep
import threading
from db_import import db, GROUPS, GUILDS, LINKED, TG_LINKED, WEBHOOKS
from tokens import TG_TOKEN

if not os.path.isdir("tempdata"):
    os.mkdir("tempdata")

access_error = 'Для данного действия необходимо обладать\nправами администратора телеграм-группы!'
bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


# class UserState(StatesGroup):
#     unlink_discord = State()
#     forecast = State()


@dp.message_handler(commands=['help', 'start', 'info', 'hey'])
async def send_welcome(message: types.Message):
    await message.reply("*__Вас приветствует RotexBot\!__*\n\n"
                        "Я разработан специально для организации двусторонней\n"
                        "связи между Telegram чатами и Discord каналами\n\n"
                        "*Команды, которые я поддерживаю:*\n"
                        "/help \- помощь\n"
                        "/id \- узнать id данной телеграм группы\n"
                        "/discord \- привязать к чату дискорд канал\n"
                        "/undiscord \- отвязать дискорд канал от чата",
                        parse_mode='MarkdownV2')


@dp.message_handler(commands=['undiscord', 'андискорд', 'unlink', 'отвязать'])
async def unlink_discord(message: types.Message):
    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if not user.is_chat_admin():
        respond = await message.reply(access_error)
        await sleep(5)
        await respond.delete()
        return

    if db.get(GROUPS, str(message.chat.id)).LINKED_CHANNEL_ID:
        buttons = [
            [
                types.InlineKeyboardButton(text="отвязать", callback_data="отвязать"),
                types.InlineKeyboardButton(text="отменить", callback_data="отменить"),
            ],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer('Вы уверены, что хотите\nотвязать дискорд сервер?', reply_markup=keyboard)
    else:
        await message.reply("Данная телеграм-группа не связана\nни с одним дискордм сервером!")


@dp.callback_query_handler()
async def callback_func(callback: types.CallbackQuery):
    chat_id = str(callback.message.chat.id)
    user = await bot.get_chat_member(int(chat_id), callback.from_user.id)
    if callback.data == 'отвязать':
        if user.is_chat_admin():
            for o in db.query(GUILDS).all():
                if o.TG_LINKED_CHANNELS_ID and db.get(TG_LINKED, chat_id).LINKED_CHANNEL_ID in o.TG_LINKED_CHANNELS_ID:
                    guild = o
                    break
            group = db.get(GROUPS, chat_id)
            linked_group = db.get(TG_LINKED, chat_id)
            linked_channel = db.get(TG_LINKED, linked_group.LINKED_CHANNEL_ID)
            webhook = db.get(WEBHOOKS, linked_channel.CHANNEL_ID)
            group.LINKED_CHANNEL_ID = None
            if ':' in guild.TG_LINKED_CHANNELS_ID:
                groups = guild.TG_LINKED_CHANNELS_ID.split(":")
                groups.remove(linked_channel.CHANNEL_ID)
                guild.TG_LINKED_CHANNELS_ID = ":".join(groups)
            else:
                guild.TG_LINKED_CHANNELS_ID = None
            db.delete(linked_group)
            db.delete(webhook)
            db.delete(linked_channel)
            db.add_all([group, guild])
            db.commit()
            await callback.message.answer('Отвязка завершена успешно!')
            await callback.message.delete()
        else:
            respond = await callback.message.reply(access_error)
            await sleep(5)
            await respond.delete()
    elif callback.data == 'отменить':
        if user.is_chat_admin():
            await callback.message.delete()
        else:
            respond = await callback.message.reply(access_error)
            await sleep(5)
            await respond.delete()


@dp.message_handler(commands=['discord', 'дискорд', 'link_discord', 'привязать_дискорд'])
async def link_discord(message: types.Message):
    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if not user.is_chat_admin():
        respond = await message.reply(access_error)
        await sleep(15)
        await respond.delete()
        return
    if db.get(GROUPS, str(message.chat.id)).LINKED_CHANNEL_ID:
        await message.reply(f'Данная телеграм группа уже связана\n'
                            f'с дискорд каналом, id которого:\n'
                            f'{db.get(GROUPS, str(message.chat.id)).LINKED_CHANNEL_ID}\n\n'
                            f'Если хотите отвязать дискорд канал,\n'
                            f'воспользуйтесь командой: /undiscord')
        return
    if ' ' in message.text:
        ds_guild_id = message.text.split()[1]
        tg_group_id = str(message.chat.id)
    else:
        await message.reply('Чтобы привязать дискорд канал к телеграм гурппе,\n'
                            'нужно установить дискорд бота Rotex\n'
                            'на целевой дискорд сервер.\n'
                            'Ссылка для приглашения дискорд бота:'
                            'https://discord.com/api/oauth2/authorize?client_id=1088509697524519115&permissions=8&scope=bot%20applications.commands\n\n'
                            'После этого, с дискорд сервера необходимо отправить\n'
                            'приглашение на создание общего чата при помощи команды\n'
                            '/link_telegram , использованной в дискорд сервере.\n\n'
                            'После того, как приглашение создать общий чат придёт\n'
                            'в эту телеграм-группу, необходимо узнать id\n'
                            'дискорд сервера,где находится канал, а затем\n'
                            'использовать команду /discord [id дисокрд сервера]\n'
                            'Чтобы завершить привязку.\n'
                            'Пример использования команды:\n\n'
                            '/discord 10832845374377255078\n\n'
                            '(узнать id дискорд сервера можно с помощью команды /id\n'
                            'использованной в желаемом дискорд сервере)')
        return

    if not db.get(GUILDS, ds_guild_id):
        await message.reply('ОШИБКА!\n'
                            'Пожалуйста, проверьте правильность введённых данных!\n\n'
                            'P.S. для работы общего telegram-discord чата\n'
                            'На дискорд сервер также необходимо пригласить бота Rotex.\n'
                            'Ссылка для приглашения дискорд-бота:\n'
                            'https://discord.com/api/oauth2/authorize?client_id=1088509697524519115&permissions=8&scope=bot%20applications.commands')
        return
    if db.get(GROUPS, tg_group_id).LINKED_CHANNEL_ID:
        await message.reply('ОШИБКА!\n'
                            'Эта группа уже связанна с дискорд сервером!\n\n'
                            'Отвязать дискорд сервер:\n'
                            '/undiscord')
    if not db.get(GUILDS, ds_guild_id).TG_LINK_WATING_GROUP_ID and not db.get(GUILDS,
                                                                              ds_guild_id).TG_LINK_WATING_CHANNEL_ID:
        await message.reply(f"На данный момент у вас нет вхожящих\n"
                            f"запросов на создание общего дискорд-телеграм чата.\n"
                            f"Если желаете установить двустороннее соединение\n"
                            f"с дискорд сервером, попросите его администратора\n"
                            f"отправить вам запрос на создание общего\n"
                            f"дискорд-телеграм чата.\n\n"
                            f"Id данной телеграм группы: {message.chat.id}")
        return
    else:
        try:
            guild_object = db.get(GUILDS, ds_guild_id)
            group_object = db.get(GROUPS, tg_group_id)
            ds_channel_id = guild_object.TG_LINK_WATING_CHANNEL_ID

            if guild_object.TG_LINKED_CHANNELS_ID:
                channels_list = guild_object.TG_LINKED_CHANNELS_ID.split(":")
                if ds_channel_id not in channels_list:
                    channels_list.append(ds_channel_id)
                guild_object.TG_LINKED_CHANNELS_ID = ":".join(channels_list)
            else:
                guild_object.TG_LINKED_CHANNELS_ID = ds_channel_id
            group_object.LINKED_CHANNEL_ID = ds_channel_id
            db.add(group_object)
            db.add(guild_object)
            db.commit()
            if not db.get(TG_LINKED, tg_group_id) and not db.get(TG_LINKED, ds_channel_id):
                channel_link = TG_LINKED(CHANNEL_ID=ds_channel_id, LINKED_CHANNEL_ID=tg_group_id)
                group_link = TG_LINKED(CHANNEL_ID=tg_group_id, LINKED_CHANNEL_ID=ds_channel_id)
                db.add(channel_link)
                db.add(group_link)
                db.commit()
            group_object.LINK_WAITING_GUILD_ID = None
            guild_object.TG_LINK_WATING_GROUP_ID = None
            guild_object.TG_LINK_WATING_CHANNEL_ID = None
            db.add(guild_object)
            db.add(group_object)
            db.commit()
            await message.reply("Привязка завершена успешно!\n"
                                "(если хотите отвязать дискорд канал,\n"
                                "воспользуйтесь /undiscord )")
        except Exception as e:
            print(e)


@dp.message_handler(commands=['id', 'айди', 'ID', 'Id', 'iD'])
async def group_id(message: types.Message):
    await message.reply(
        f"Айди данной телеграмм группы:\n\n{message.chat.id}\n\nВнимание! Минус перед цифрами (если он есть)\nтак же является частью id!")


@dp.message_handler(content_types=['new_chat_members'])
async def join_group(message: types.Message):
    bot_object = await bot.get_me()
    chat_id = str(message.chat.id)
    for chat_member in message.new_chat_members:
        if chat_member.id == bot_object.id and not db.get(GROUPS, chat_id):
            GROUP = GROUPS(GROUP_ID=chat_id)
            db.add(GROUP)
            db.commit()
    print(f"Телеграм бот стал членом группы с айди:   {chat_id}")


@dp.message_handler(content_types=['left_chat_member'])
async def leave_group(message: types.Message):
    bot_object = await bot.get_me()
    chat_id = str(message.chat.id)
    if message.left_chat_member.id == bot_object.id and db.get(GROUPS, chat_id):
        db.delete(db.get(GROUPS, chat_id))

        if db.get(TG_LINKED, chat_id):
            channel_id = db.get(TG_LINKED, chat_id).LINKED_CHANNEL_ID
            db.delete(db.get(TG_LINKED, chat_id))
            db.delete(db.get(TG_LINKED, channel_id))
        if db.get(WEBHOOKS, channel_id):
            db.delete(db.get(WEBHOOKS, channel_id))
        for guild_object in db.query(GUILDS).all():
            if guild_object.TG_LINKED_CHANNELS_ID and channel_id in guild_object.TG_LINKED_CHANNELS_ID.split(':'):
                if ':' in guild_object.TG_LINKED_CHANNELS_ID:
                    channels_list = guild_object.TG_LINKED_CHANNELS_ID.split(":")
                    channels_list.remove(channel_id)
                    guild_object.TG_LINKED_CHANNELS_ID = ":".join(channels_list)
                else:
                    guild_object.TG_LINKED_CHANNELS_ID = None
                    db.add(guild_object)
                break
        db.commit()
    print(f"Телеграм бот покинул группу с айди:   {chat_id}")


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def resend(message: types.Message):
    if not db.get(GROUPS, str(message.chat.id)):
        return
    if db.get(GROUPS, str(message.chat.id)).LINKED_CHANNEL_ID:
        try:
            text = None
            files = []
            file_size_error = 'Вложение не было доставлено в дискорд канал из за превышения допустимого размера(25Mb)'

            if message.text:
                text = message.text
            if message.voice:
                if message.voice.file_size >= 26214400:
                    respond = await message.reply(file_size_error)
                    await sleep(15)
                    await respond.delete()
                else:
                    file = await bot.get_file(message.voice.file_id)
                    await bot.download_file(file.file_path, f'tempdata/voice_message.mp3')
                    files.append(discord.File('tempdata/voice_message.mp3'))
            elif message.audio:
                if message.audio.file_size >= 26214400:
                    respond = await message.reply(file_size_error)
                    await sleep(15)
                    await respond.delete()
                else:
                    file = await bot.get_file(message.audio.file_id)
                    await bot.download_file(file.file_path, f'tempdata/{message.audio.title}.mp3')
                    files.append(discord.File(f'tempdata/{message.audio.title}.mp3'))
                text = message.caption
            elif message.photo:
                if message.photo[-1]['file_size'] >= 26214400:
                    respond = await message.reply(file_size_error)
                    await sleep(15)
                    await respond.delete()
                else:
                    file = await bot.get_file(message.photo[-1]["file_id"])
                    await bot.download_file(file.file_path,
                                            f'tempdata/{message.photo[-1].file_unique_id}.{file.file_path.split(".")[-1]}')
                    files.append(
                        discord.File(f'tempdata/{message.photo[-1].file_unique_id}.{file.file_path.split(".")[-1]}'))
                text = message.caption
            elif message.video:
                if message.video.file_size >= 26214400:
                    respond = await message.reply(file_size_error)
                    await sleep(15)
                    await respond.delete()
                else:
                    file = await bot.get_file(message.video.file_id)
                    await bot.download_file(file.file_path, f'tempdata/{message.video.file_name}')
                    files.append(discord.File(f'tempdata/{message.video.file_name}'))
                text = message.caption
            elif message.video_note:
                if message.video_note.file_size >= 26214400:
                    respond = await message.reply(file_size_error)
                    await sleep(15)
                    await respond.delete()
                else:
                    file = await bot.get_file(message.video_note.file_id)
                    await bot.download_file(file.file_path,
                                            f'tempdata/videomessage_from_{message.from_user.first_name}.{file.file_path.split(".")[-1]}')
                    files.append(discord.File(
                        f'tempdata/videomessage_from_{message.from_user.first_name}.{file.file_path.split(".")[-1]}'))
            elif message.animation:
                if message.animation.file_size >= 26214400:
                    respond = await message.reply(file_size_error)
                    await sleep(15)
                    await respond.delete()
                else:
                    file = await bot.get_file(message.animation.file_id)
                    if not file.file_path.endswith('tgs'):
                        await bot.download_file(file.file_path, f'tempdata/{message.animation.file_name}')
                        files.append(discord.File(f'tempdata/{message.animation.file_name}'))
                text = message.caption
            elif message.document:
                if message.document.file_size >= 26214400:
                    respond = await message.reply(file_size_error)
                    await sleep(15)
                    await respond.delete()
                else:
                    file = await bot.get_file(message.document.file_id)
                    await bot.download_file(file.file_path, f'tempdata/{message.document.file_name}')
                    files.append(discord.File(f'tempdata/{message.document.file_name}'))
                text = message.caption
            elif message.sticker:
                if message.sticker.file_size >= 26214400:
                    respond = await message.reply(file_size_error)
                    await sleep(15)
                    await respond.delete()
                else:
                    file = await bot.get_file(message.sticker.file_id)
                    if file.file_path.endswith('tgs'):
                        pass
                    else:
                        await bot.download_file(file.file_path,
                                                f'tempdata/{message.sticker.file_unique_id}.{file.file_path.split(".")[-1]}')
                        files.append(
                            discord.File(f'tempdata/{message.sticker.file_unique_id}.{file.file_path.split(".")[-1]}'))
                text = message.caption
            try:
                if text or files:
                    webhook = SyncWebhook.from_url(
                        db.get(WEBHOOKS, (db.get(GROUPS, str(message.chat.id)).LINKED_CHANNEL_ID)).WEBHOOK_URL)
                    webhook.send(content=text,
                                 username=f'{message.from_user.first_name}〔TG〕',
                                 avatar_url="https://logos-download.com/wp-content/uploads/2016/07/Telegram_2.x_version_2014_Logo.png",
                                 files=files)
            except Exception as e:
                await message.answer(f"Если вы видите данное сообщение,\n"
                                     f"значит произошла программная ошибка,\n"
                                     f"из за которой сообщение не было доставлено\n"
                                     f"в дискорд канал, связанный с данной группой\.\n\n"
                                     f"Приносим свои извинения за произошедшее, отчёт\n"
                                     f"о сбое уже оправлен разработчикам для\n"
                                     f"вяснения причин и устранения неполадок\."
                                     f"Если данная ошибка стала появляться регулярно,\n"
                                     f"воспользуйтесь /undiscord , а затем перенастройте связь\n"
                                     f"с дискород-сервером с помощью /discord"
                                     f"Код ошибки:\n"
                                     f"```{e}```", parse_mode="'MarkdownV2")
                print(f"АХТУНГ!!! АХТУНГ!!! АХТУНГ!!!\n"
                      f"сбой в работе ds-tg канала (ошибка вебхука). Код ошибки:\n"
                      f"{e}")
        except Exception as e:
            await message.answer(f"Если вы видите данное сообщение,\n"
                                 f"значит произошла программная ошибка,\n"
                                 f"из за которой сообщение не было доставлено\n"
                                 f"в дискорд канал, связанный с данной группой\.\n\n"
                                 f"Приносим свои извинения за произошедшее, отчёт\n"
                                 f"о сбое уже оправлен разработчикам для\n"
                                 f"вяснения причин и устранения неполадок\."
                                 f"Если данная ошибка стала появляться регулярно,\n"
                                 f"воспользуйтесь /undiscord , а затем перенастройте связь\n"
                                 f"с дискород-сервером с помощью /discord"
                                 f"Код ошибки:\n"
                                 f"```{e}```", parse_mode="'MarkdownV2")
            print(f"АХТУНГ!!! АХТУНГ!!! АХТУНГ!!!\n"
                  f"сбой в работе ds-tg канала. Код ошибки:\n"
                  f"{e}")


def ready():
    print('Telegram-bot started successfully!')


def clearing():
    while True:
        sleep(60)
        try:
            shutil.rmtree('tempdata')
            os.mkdir("tempdata")
        except:
            continue


t = threading.Thread(target=clearing, daemon=True)
t.start()
executor.start_polling(dp, on_startup=ready())

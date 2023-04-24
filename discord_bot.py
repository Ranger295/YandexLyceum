from statistics import mean, mode
import datetime
import discord
import json
import asyncio
import requests
from discord import Option
from discord.ext import commands
from db_import import db, GROUPS, GUILDS, LINKED, TG_LINKED, WEBHOOKS
from tokens import DS_TOKEN, TG_TOKEN
from commands import commands_info

COMMAND_LIST = \
    """
    `r!hey` - проверить, жив ли я
    `r!mute` - отправить участника в таймаут
    `r!unmute` - снять таймаут с участника
    `r!clear` - очистить выбранное кол-во сообщений
    `r!post` - создать эмбед по json-шаблону
    
    `/help`
    `/stats` - получить статистику пользователя
    `/weather` - прогноз погоды на 5 дней
    `/id` - список id всех каналов сервера
    `/post_help` - инструкция по созданию эмбедов
    `/link_discord` - общий канал с другим дискорд сервером
    `/link_telegram` - общий канал с телеграм-группой
    `/unlink_telegram` - отвязать телеграмм   
    """

bot = commands.Bot(command_prefix='r!', intents=discord.Intents.all(), help_command=None)
BOT_IS_READY = False


@bot.slash_command(name='help', description='обзор фукнционала бота')
async def help(ctx,
               command: Option(str, description="Выберите команду, чтобы познакомиться с ней поближе",
                               choices=["r!mute", "r!unmute", "r!clear", "r!post",
                                        "/help", "/stats", "/weather", "/id", "/post_help",
                                        "/link_discord", "/link_telegram", "/unlink_telegram"],
                               required=False)):
    if not command:
        embed = discord.Embed(title="` Список доступных команд `",
                              description=f"```Основной задачей бота является\n"
                                          f"простое и доступное каждому объединение\n"
                                          f"телеграм-группы и дискорд канала в один чат.\n"
                                          f"Также, бот позволяет создавать общие каналы\n"
                                          f"между дружескими дискорд серверами.```\n"
                                          f"**Используйте `/help название_команды` , чтобы\n"
                                          f"узнать больше об интересующей команде.**\n"
                                          f"{COMMAND_LIST}",
                              color=0x1e1f22)
        await ctx.respond(embed=embed)
    else:
        embed = discord.Embed(title=f"` {command} `",
                              description=commands_info[command],
                              color=0x1e1f22)
        await ctx.respond(embed=embed, ephemeral=True, delete_after=450)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.author.discriminator != '0000':
        if (db.get(GUILDS, str(message.guild.id))).TG_LINKED_CHANNELS_ID and \
                str(message.channel.id) in (db.get(GUILDS, str(message.guild.id))).TG_LINKED_CHANNELS_ID:
            try:
                url = f"https://api.telegram.org/bot{TG_TOKEN}"
                tg_chat_id = db.get(TG_LINKED, str(message.channel.id)).LINKED_CHANNEL_ID
                author = []
                for sign in f'{message.author.name}':
                    if sign in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.',
                                '!']:
                        author.append(f'\{sign}')
                    else:
                        author.append(sign)
                author = "".join(author)
                message_author = f"*[{author} 〔DS〕](tg://user?id={bot.user.id})*\n"
                tg_message = []
                if message.content:
                    for sign in message.content:
                        if sign in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.',
                                    '!']:
                            tg_message.append(f'\{sign}')
                        else:
                            tg_message.append(sign)
                    tg_message = message_author + "".join(tg_message)
                else:
                    tg_message = message_author

                method = url + "/sendMessage"
                r = requests.post(method, data={
                    "chat_id": tg_chat_id,
                    "text": tg_message,
                    "parse_mode": "MarkdownV2"
                })
                if r.status_code != 200:
                    raise Exception("ТЕКСТ ЕГГОР! Код НЕ 200!")
                if len(message.attachments) > 0:
                    for attach in message.attachments:
                        await attach.save(f'tempdata/{attach.filename}')
                        if attach.content_type:
                            file_type = attach.content_type.split('/')[0]
                        else:
                            file_type = None
                        if file_type == 'image':
                            if attach.filename.endswith('gif'):
                                files = {'animation': open(f'tempdata/{attach.filename}', 'rb')}
                                r = requests.post(url + "/sendAnimation?chat_id=" + tg_chat_id, files=files)
                                if r.status_code != 200:
                                    raise Exception("ФОТО ЕГГОР! Код НЕ 200!")
                            else:
                                files = {'photo': open(f'tempdata/{attach.filename}', 'rb')}
                                r = requests.post(url + "/sendPhoto?chat_id=" + tg_chat_id, files=files)
                                if r.status_code != 200:
                                    raise Exception("ГИФ ЕГГОР! Код НЕ 200!")
                        elif file_type == 'application' or file_type == 'text' or not file_type:
                            files = {'document': open(f'tempdata/{attach.filename}', 'rb')}
                            r = requests.post(url + "/sendDocument?chat_id=" + tg_chat_id, files=files)
                            if r.status_code != 200:
                                raise Exception("ФАЙЛ ЕГГОР! Код НЕ 200!")
                        elif file_type == 'video':
                            files = {'video': open(f'tempdata/{attach.filename}', 'rb')}
                            r = requests.post(url + "/sendVideo?chat_id=" + tg_chat_id, files=files)
                            if r.status_code != 200:
                                raise Exception("ВИДЕО ЕГГОР! Код НЕ 200!")
                        elif file_type == 'audio':
                            files = {'audio': open(f'tempdata/{attach.filename}', 'rb')}
                            r = requests.post(url + "/sendAudio?chat_id=" + tg_chat_id, files=files)
                            if r.status_code != 200:
                                raise Exception("АУДИО ЕГГОР! Код НЕ 200!")
            except Exception as e:
                await message.answer(f"Если вы видите данное сообщение,\n"
                                     f"значит произошла программная ошибка,\n"
                                     f"из за которой сообщение не было доставлено\n"
                                     f"в телеграм-группу, связанную с данным дискорд каналом.\n\n"
                                     f"Приносим свои извинения за произошедшее, отчёт\n"
                                     f"о сбое уже оправлен разработчикам для\n"
                                     f"вяснения причин и устранения неполадок\."
                                     f"Если данная ошибка стала появляться регулярно,\n"
                                     f"воспользуйтесь /unlink_telegram , а затем перенастройте связь\n"
                                     f"с телеграмм-группой с помощью /link_telegram"
                                     f"Код ошибки:\n"
                                     f"```{e}```")

        if (db.get(GUILDS, str(message.guild.id))).LINKED_CHANNELS_ID and \
                str(message.channel.id) in (db.get(GUILDS, str(message.guild.id))).LINKED_CHANNELS_ID:
            # await message.reply(f'Id гильдии: {str(message.guild.id)}\nId канала: {str(message.channel.id)}\nLinked channels id: {(db.get(GUILDS, str(message.guild.id))).LINKED_CHANNELS_ID}\n')
            linked_channels_list = (((db.get(LINKED, str(message.channel.id))).LINKED_CHANNELS_ID).split(':'))
            for channel in linked_channels_list:
                try:
                    webhooks = await (bot.get_channel(int(channel))).webhooks()
                    webhook_exists = False
                    for webhook in webhooks:
                        if webhook.user == bot.user and webhook.name == 'Cross_Server_Chat_Webhook':
                            webhook_exists = True
                            break
                    if not webhook_exists:
                        webhook = await (bot.get_channel(int(channel))).create_webhook(name='Cross_Server_Chat_Webhook')
                    message_files = []
                    message_embeds = []
                    if len(message.attachments) > 0:
                        for attach in message.attachments:
                            file = await attach.to_file()
                            message_files.append(file)
                    if len(message.embeds) > 0 and 'https://' not in message.content and 'http://' not in message.content:
                        message_embeds = message.embeds
                    await webhook.send(message.content,
                                       username=f"{message.author.name}〔{message.author.guild.name}〕",
                                       avatar_url=message.author.avatar, files=message_files, embeds=message_embeds)
                except:
                    if not bot.get_channel(int(channel)):
                        for linked_channel_id in db.get(LINKED, channel).LINKED_CHANNELS_ID.split(':'):
                            linked_channel = db.get(LINKED, linked_channel_id)
                            channels = linked_channel.LINKED_CHANNELS_ID.split(":")
                            channels.remove(channel)
                            linked_channel.LINKED_CHANNELS_ID = ":".join(channels)
                            if not linked_channel.LINKED_CHANNELS_ID:
                                db.delete(linked_channel)
                            else:
                                db.add(linked_channel)
                            db.commit()
                            for o in db.query(GUILDS).all():
                                if o.LINKED_CHANNELS_ID and linked_channel_id in o.LINKED_CHANNELS_ID:
                                    if not db.get(LINKED, linked_channel_id):
                                        channels = o.LINKED_CHANNELS_ID.split(":")
                                        channels.remove(linked_channel_id)
                                        o.LINKED_CHANNELS_ID = ":".join(channels)
                                        if not o.LINKED_CHANNELS_ID:
                                            o.LINKED_CHANNELS_ID = None
                                        db.add(o)
                                        db.commit()
                                if o.LINKED_CHANNELS_ID and channel in o.LINKED_CHANNELS_ID:
                                    channels = o.LINKED_CHANNELS_ID.split(":")
                                    channels.remove(channel)
                                    o.LINKED_CHANNELS_ID = ":".join(channels)
                                    if not o.LINKED_CHANNELS_ID:
                                        o.LINKED_CHANNELS_ID = None
                                    db.add(o)
                                    db.commit()
                        db.delete(db.get(LINKED, channel))
                        db.commit()

    if len(message.content) >= 6 and message.content[:6] == 'r!post':
        if not message.author.guild_permissions.manage_messages:
            embed = discord.Embed(title='**` ОШИБКА! `**',
                                  description='**Вам необходимо обладать правом на "управление сообщениями"**\n'
                                              '**Что бы использовать эту команду.**\n'
                                              '**Подробнее о том, как создавать эмбеды:**\n'
                                              '`/post_help`',
                                  color=0xff0000)
            await message.channel.send(embed=embed, delete_after=15.0)
            return
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type.split("/")[0] != "image":
                    embed = discord.Embed(title='**` ОШИБКА! `**',
                                          description='**` Неверный формат вложений. `**\n'
                                                      '**Embed может содержать только изображения!**\n'
                                                      '**Подробнее о том, как создавать эмбеды:**\n'
                                                      '`/post_help`',
                                          color=0xff0000)
                    await message.delete()
                    await message.channel.send(embed=embed, delete_after=15.0)
                    return
        try:
            avatar = bot.user.avatar
            name = bot.user.name
            embeds_data = json.loads(f"[{message.content[7:]}]", strict=False)
            embeds = []
            embed_index = 0
            for embed_dict in embeds_data:
                title = None
                description = None
                if "title" in embed_dict.keys():
                    title = embed_dict["title"]
                if "text" in embed_dict.keys():
                    description = embed_dict["text"]
                if "color" in embed_dict.keys():
                    color = int(embed_dict["color"].replace('#', ''), 16)
                else:
                    color = int("2b2d31", 16)
                embed = discord.Embed(title=title, description=description, color=color)
                if "footer" in embed_dict.keys():
                    embed.set_footer(text=embed_dict["footer"])
                if "smallimage" in embed_dict.keys():
                    embed.set_thumbnail(url=embed_dict["smallimage"])
                if "image" in embed_dict.keys():
                    embed.set_image(url=embed_dict["image"])
                if message.attachments:
                    if embed_index < len(message.attachments):
                        embed.set_image(url=((message.attachments[embed_index]).url))
                if "avatar" in embed_dict.keys():
                    avatar = embed_dict["avatar"]
                if "name" in embed_dict.keys():
                    name = embed_dict["name"]
                embeds.append(embed)
                embed_index += 1

            webhook = await message.channel.create_webhook(name='Rotex_Embed_Webhook')
            await message.delete()
            await webhook.send(username=name, avatar_url=avatar, embeds=embeds)
            await webhook.delete()
        except Exception as e:
            print(e)
            await message.delete()
            embed = discord.Embed(title='**` ОШИБКА! `**',
                                  description='**Неверный Json формат!**\n'
                                              '**Подробнее о том, как создавать эмбеды:**\n'
                                              '`/post_help`',
                                  color=0xff0000)
            await message.channel.send(embed=embed, delete_after=7.0)
    await bot.process_commands(message)


@bot.slash_command(name='post_help', description='подробное руководство по созданию эмбед-сообщений')
async def post_help(ctx):
    embed = discord.Embed(title='**` Полное руководство по эмбед-сообщениям `**',
                          description=commands_info["full_embed_tutorial"],
                          color=0x1e1f22)
    await ctx.respond(embed=embed)


@bot.slash_command(name='link_discord', description='Создать общий чат с другим дисокрд сервером')
@discord.ext.commands.has_guild_permissions(administrator=True)
async def link_discord(ctx,
                       guild_id: Option(str, description="Введите id дискорд сервера: ", required=True),
                       channel: Option(str, description="Введите id канала, который станет общим чатом: ",
                                       required=True)):
    if not bot.get_guild(int(guild_id)) or not bot.get_channel(int(channel)):
        embed = discord.Embed(title="**` ОШИБКА! `**",
                              description=f"**Некорректный дискорд сервер или\n"
                                          f"указан несуществующий канал.\n\n"
                                          f"Если вы уверены, что данные введены\n"
                                          f"правильно, пожалуйста, убедитесь в том,\n"
                                          f"что {bot.user.mention} установлен\n"
                                          f" на обоих дискорд серверах.**",
                              color=0xff0000)
        await ctx.respond(embed=embed, ephemeral=True)
        return
    if db.get(GUILDS, str(ctx.guild.id)).LINKED_CHANNELS_ID and \
            len(db.get(GUILDS, str(ctx.guild.id)).LINKED_CHANNELS_ID.split(':')) >= 3:
        embed = discord.Embed(title="**` ОШИБКА! `**",
                              description=f"**` У вас уже есть 3 общих чата с другими серверами! `**\n"
                                          f"**Максимальное количество каналов для одного сервера,\n"
                                          f"связанных с другими дискорд серверами сотавляет __3 канала__.\n"
                                          f"Удалите один из 3 cross-server каналов,\n"
                                          f"если хотите привязать новый!**\n\n"
                                          f"__*(Информация о всех общих чатах: /serverinfo)*__",
                              color=0xff0000)
        await ctx.respond(embed=embed, ephemeral=True)
        return

    if not bot.get_guild(int(guild_id)).system_channel:
        embed = discord.Embed(title="**` ОШИБКА! `**",
                              description=f"**На дискорд сервере `{bot.get_guild(int(guild_id)).name}`\n"
                                          f"не выбран канал системных сообщений.\n\n"
                                          f"Чтобы приглашение дошло до адресата, Администраторам\n"
                                          f"дискорд сервера `{bot.get_guild(int(guild_id)).name}`\n"
                                          f"необходимо выбрать канал для системных сообщений.\n"
                                          f"Сделать это можно в настройках дисокрд сервера,\n"
                                          f"в разделе «Обзор».**",
                              color=0xff0000)
        await ctx.respond(embed=embed, ephemeral=True)
        return
    if db.get(LINKED, channel):
        for channel_ in (db.get(LINKED, channel).LINKED_CHANNELS_ID).split(":"):
            if not bot.get_channel(int(channel_)):
                for linked_channel_id in db.get(LINKED, channel_).LINKED_CHANNELS_ID.split(':'):
                    linked_channel = db.get(LINKED, linked_channel_id)
                    channels = linked_channel.LINKED_CHANNELS_ID.split(":")
                    channels.remove(channel_)
                    linked_channel.LINKED_CHANNELS_ID = ":".join(channels)
                    if not linked_channel.LINKED_CHANNELS_ID:
                        db.delete(linked_channel)
                    else:
                        db.add(linked_channel)
                    db.commit()
                    for o in db.query(GUILDS).all():
                        if o.LINKED_CHANNELS_ID and linked_channel_id in o.LINKED_CHANNELS_ID:
                            if not db.get(LINKED, linked_channel_id):
                                channels = o.LINKED_CHANNELS_ID.split(":")
                                channels.remove(linked_channel_id)
                                o.LINKED_CHANNELS_ID = ":".join(channels)
                                if not o.LINKED_CHANNELS_ID:
                                    o.LINKED_CHANNELS_ID = None
                                db.add(o)
                                db.commit()
                        if o.LINKED_CHANNELS_ID and channel_ in o.LINKED_CHANNELS_ID:
                            channels = o.LINKED_CHANNELS_ID.split(":")
                            channels.remove(channel_)
                            o.LINKED_CHANNELS_ID = ":".join(channels)
                            if not o.LINKED_CHANNELS_ID:
                                o.LINKED_CHANNELS_ID = None
                            db.add(o)
                            db.commit()
                db.delete(db.get(LINKED, channel_))
                db.commit()
    if db.get(LINKED, channel) and guild_id in \
            [str((bot.get_channel(int(channel_))).guild.id) for channel_ in \
             (db.get(LINKED, channel).LINKED_CHANNELS_ID).split(":")]:
        embed = discord.Embed(title="**` ОШИБКА! `**",
                              description=f"**Канал уже слинкован с ` {bot.get_guild(int(guild_id))} `**",
                              color=0xff0000)
        await ctx.respond(embed=embed, delete_after=15.0, ephemeral=True)
        return
    if guild_id in [str(guild.id) for guild in bot.guilds] and \
            channel in [str(channel_.id) for channel_ in bot.get_all_channels()]:
        guild_object = db.get(GUILDS, str(ctx.guild.id))
        guild_object.LINK_WAITING_CHANNEL_ID = channel
        db.add(guild_object)
        db.commit()
        guilds = ""
        if (db.get(LINKED, channel)):
            guilds = "` " + "` \n `".join([(bot.get_channel(int(channel_))).guild.name for channel_ in \
                                           ((db.get(LINKED, channel)).LINKED_CHANNELS_ID).split(':') if \
                                           (bot.get_channel(int(channel_)))]) + " `"
        other_guild = bot.get_guild(int(guild_id))
        other_guild_channel = other_guild.system_channel
        other_guild_embed = discord.Embed(title="` ПРИГЛАШЕНИЕ ПРИСОЕДИНИТЬСЯ К ОБЩЕМУ КАНАЛУ `",
                                          description=f"**Здравствуйте, уважаемый {other_guild.owner.mention}!\n\n"
                                                      f"Дискорд сервер **` {ctx.guild.name} `**\n"
                                                      f"приглашает вас присоединится к общему каналу.**\n"
                                                      f"` Сервера-участники: `\n\n"
                                                      f"` {ctx.guild.name} `\n"
                                                      f"{guilds}",
                                          color=0x00BF32)
        other_guild_embed.set_footer(text=f'id приглащающего сервера: |{ctx.guild.id}|')
        await other_guild_channel.send(embed=other_guild_embed,
                                       view=link_channel_request())
        embed = discord.Embed(title="` ЗАПРОС ОТПРАВЛЕН! `",
                              description=f"**Приглашение на присоединение \n"
                                          f"сервера **` {other_guild.name} `**\n"
                                          f"к общему каналу <#{channel}>\n"
                                          f"отправлено успешно!\n"
                                          f"(Отправлено в канал <#{other_guild_channel.id}>)\n\n"
                                          f"__Пожалуйста, ожидайте принятия приглашения.__**",
                              color=0x00BF32)
        await ctx.respond(embed=embed)
    else:
        embed = discord.Embed(title="**` ОШИБКА! `**",
                              description=f"**Некорректный дискорд сервер или\n"
                                          f"указан несуществующий канал.\n\n"
                                          f"Если вы уверены, что данные введены\n"
                                          f"правильно, пожалуйста, убедитесь в том,\n"
                                          f"что {bot.user.mention} установлен\n"
                                          f" на обоих дискорд серверах.**",
                              color=0xff0000)
        await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name='link_telegram',
                   description='Создать общий чат с телеграм-группой (Подробнее: /help link_telegram)')
@discord.ext.commands.has_guild_permissions(administrator=True)
async def link_telegram(ctx,
                        group_id: Option(str, description="Введите id телеграм-группы: ", required=True),
                        channel_id: Option(str, description="Введите id канала, который станет общим чатом: ",
                                           required=True)):
    guild_id = str(ctx.guild.id)
    error_message_embed = discord.Embed(title='**` ОШИБКА `**',
                                        description="Проверьте правильность введённых данных,\n"
                                                    "а также убедитесь в том, что [**__RotexBot__**](https://t.me/R7Bot_bot):\n"
                                                    "установлен в целевой телеграм-группе!\n\n"
                                                    "__Подробнее в:__ `/help link_telegram `",
                                        color=0xff0000)
    if not db.get(GROUPS, group_id) or not bot.get_channel(int(channel_id)):
        await ctx.respond(embed=error_message_embed, ephemeral=True)
        return

    if db.get(GUILDS, guild_id).TG_LINKED_CHANNELS_ID and \
            len(db.get(GUILDS, guild_id).TG_LINKED_CHANNELS_ID.split(':')) >= 3:
        embed = discord.Embed(title="**` ОШИБКА! `**",
                              description=f"**` У вас уже есть 3 общих чатов с другими тг-группами! `**\n"
                                          f"**Максимальное количество каналов для одного сервера,\n"
                                          f"связанных с другими телеграм-группами сотавляет __3 канала__.\n"
                                          f"Отвяжите один из 3 каналов, уже связанных с телеграмом\n"
                                          f"если хотите привязать новый!\n"
                                          f"Отвязать телеграм группу:** `/unlink_telegram`\n\n"
                                          f"__*(Информация о всех общих чатах: /serverinfo)*__",
                              color=0xff0000)
        await ctx.respond(embed=embed, ephemeral=True)
        return
    if db.get(GROUPS, group_id).LINKED_CHANNEL_ID:
        embed = discord.Embed(title='**` ОШИБКА `**',
                              description='Данная телеграм группа уже связана с дискород сервером!\n'
                                          'Выберите другой телеграм-чат, или попросите администратора\n'
                                          'телеграм-группы отвязать её с помощью /undiscord команды.',
                              color=0xff0000)
        await ctx.respond(embed=embed, delete_after=30.0, ephemeral=True)
        return
    if db.get(GUILDS, guild_id).LINKED_CHANNELS_ID and \
            channel_id in db.get(GUILDS, guild_id).LINKED_CHANNELS_ID.split(":"):
        embed = discord.Embed(title='**` ОШИБКА `**',
                              description='Выбранный канал уже связан с дискород сервером!\n'
                                          'Пожалуйста, выберите другой канал!',
                              color=0xff0000)
        await ctx.respond(embed=embed, delete_after=30.0, ephemeral=True)
        return
    if db.get(GUILDS, guild_id).TG_LINKED_CHANNELS_ID and \
            channel_id in db.get(GUILDS, guild_id).TG_LINKED_CHANNELS_ID.split(':'):
        embed = discord.Embed(title='**` ОШИБКА `**',
                              description='Выбранный дискорд канал уже связан с телеграм группой!\n'
                                          'Выберите другой канал, или отвяжите телеграм-группу\n'
                                          'от канала с помощью команды `/unlink_telegram`!',
                              color=0xff0000)
        await ctx.respond(embed=embed, delete_after=30.0, ephemeral=True)
        return
    else:
        try:
            tg_message = f"〔〔 СИСТЕМНОЕ СООБЩЕНИЕ 〕〕\n\n" \
                         f"Дискорд сервер «{ctx.guild.name}»\n" \
                         f"приглашает ваш Telegram канал создать общий чат!\n" \
                         f"Чтобы завершить создание общего канала, введите:\n\n" \
                         f"/discord {guild_id}\n"
            url = f"https://api.telegram.org/bot{TG_TOKEN}"
            method = url + "/sendMessage"
            r = requests.post(method, data={
                "chat_id": int(group_id),
                "text": tg_message
            })
            if r.status_code != 200:
                raise Exception("ЕГГОР! Код НЕ 200!")

            guild_object = db.get(GUILDS, guild_id)
            guild_object.TG_LINK_WATING_GROUP_ID = group_id
            guild_object.TG_LINK_WATING_CHANNEL_ID = channel_id
            db.add(guild_object)
            db.commit()

            webhooks = await (bot.get_channel(int(channel_id))).webhooks()
            for webhook in webhooks:
                if webhook.user == bot.user and webhook.name == 'RotexBot_telegram_connection_webhook':
                    await webhook.delete()
            tg_webhook = await (bot.get_channel(int(channel_id))).create_webhook(
                name='RotexBot_telegram_connection_webhook')
            db.add(WEBHOOKS(CHANNEL_ID=channel_id, WEBHOOK_URL=tg_webhook.url))
            db.commit()

            embed = discord.Embed(title="**` ЗАПРОС ОТПРАВЛЕН УСПЕШНО! `**",
                                  description=f"**Чтобы завершить установку соединения, пожалуйста,\n"
                                              f"введите в телеграм-группе следующую команду:**\n\n"
                                              f"`/discord {guild_id}`",
                                  colour=0x00BF32)
            await ctx.respond(embed=embed)
        except Exception as e:
            print(e)


@discord.ext.commands.has_guild_permissions(administrator=True)
@bot.slash_command(name='unlink_telegram',
                   description='Отвязать общий дискорд-телеграм чат(Подробнее: /help unlink_telegram)')
async def unlink_telegram(ctx,
                          group_id: Option(str, description="Введите id телеграм-группы, которую желаете отвязать.",
                                           required=True)):
    if db.get(GROUPS, group_id) and db.get(GROUPS, group_id).LINKED_CHANNEL_ID and \
            bot.get_channel(int(db.get(GROUPS, group_id).LINKED_CHANNEL_ID)) in ctx.guild.text_channels:
        embed = discord.Embed(title="**` ПОДТВЕРДИТЕ ДЕЙСТВИЕ `**",
                              description=f"**Вы уверены, что хотите разорвать\n"
                                          f"соединение, отключив общий чат между\n"
                                          f"дискорд каналом <#{db.get(GROUPS, group_id).LINKED_CHANNEL_ID}>\n"
                                          f"и телеграмм группой с id `{group_id}`?**",
                              color=0xff0000)
        embed.set_footer(text=f'id выбранной телеграм-группы: |{group_id}|')
        await ctx.respond(embed=embed, view=Buttons_unlink_telegram(), ephemeral=True)

    else:
        embed = discord.Embed(title="**` ОШИБКА `**",
                              description=f"**Пожалуйста, проверьте корректность\n"
                                          f"введённых данных и попробуйте ещё раз!**",
                              color=0xff0000)
        await ctx.respond(embed=embed, delete_after=15.0, ephemeral=True)


@bot.command()
async def hey(ctx):
    await ctx.reply(f"I am alive!", mention_author=False)


@bot.command()
@discord.ext.commands.has_guild_permissions(manage_messages=True)
async def clear(ctx, limit):
    limit = int(limit) + 1
    embed = discord.Embed(title=f"Очищено `{limit - 1}` сообщений в <#{ctx.channel.id}>:", color=0xff0000,
                          timestamp=datetime.datetime.utcnow())
    embed.set_footer(text=f'Модератор: {ctx.author}')
    await ctx.channel.purge(limit=limit)
    await ctx.send(embed=embed, delete_after=10.0)


@bot.command()
@discord.ext.commands.has_guild_permissions(mute_members=True)
async def mute(ctx, member: discord.Member, time, *reason):
    if not reason:
        reason = ['не указана.']
    if time[-1] not in 'smhd':
        time = f'{time}h'
    if time[-1] == 's':
        if time[-2] in '1':
            full_time = f'{time[:-1]} секунду'
        elif time[-2] in '234':
            full_time = f'{time[:-1]} секунды'
        elif time[-2] in '567890':
            full_time = f'{time[:-1]} секунд'
        time = int(time[0:-1])
        until = (datetime.datetime.utcnow() + datetime.timedelta(seconds=time))
    elif time[-1] == 'm':
        if time[-2] in '1':
            full_time = f'{time[:-1]} минуту'
        elif time[-2] in '234':
            full_time = f'{time[:-1]} минуты'
        elif time[-2] in '567890':
            full_time = f'{time[:-1]} минут'
        time = int(time[0:-1])
        until = (datetime.datetime.utcnow() + datetime.timedelta(minutes=time))
    elif time[-1] == 'h':
        if time[-2] in '1':
            full_time = f'{time[:-1]} час'
        elif time[-2] in '234':
            full_time = f'{time[:-1]} часа'
        elif time[-2] in '567890':
            full_time = f'{time[:-1]} часов'
        time = int(time[0:-1])
        until = (datetime.datetime.utcnow() + datetime.timedelta(hours=time))
    elif time[-1] == 'd':
        if int(time[:-1]) > 28:
            await ctx.reply('Из за ограничений дискорда невозможно выдать мут более, чем на 28 дней!', delete_after=5.0)
            await asyncio.sleep(5)
            await ctx.message.delete()
        if time[-2] in '1':
            full_time = f'{time[:-1]} день'
        elif time[-2] in '234':
            full_time = f'{time[:-1]} дня'
        elif time[-2] in '567890':
            full_time = f'{time[:-1]} дней'
        time = int(time[0:-1])
        until = (datetime.datetime.utcnow() + datetime.timedelta(days=time))

    await member.timeout(until, reason=None)
    await ctx.message.delete()
    embed = discord.Embed(title=f"Хоба!",
                          description=f"{member.mention} был выдан мут на {full_time}. \n`Причина:` {' '.join(reason)}",
                          color=0xff0000)
    embed.set_footer(text=f'Участника замутил {ctx.author}')
    await ctx.send(embed=embed, delete_after=3600.0)


@bot.command()
@discord.ext.commands.has_guild_permissions(mute_members=True)
async def unmute(ctx, member: discord.Member):
    time = 0
    until = (datetime.datetime.utcnow() + datetime.timedelta(minutes=time))
    await member.timeout(until, reason=None)
    await ctx.message.delete()
    embed = discord.Embed(title=f"Ура!", description=f"С участника {member.mention} был снят мут.", color=0x00BF32)
    embed.set_footer(text=f'Участника размутил {ctx.author}')
    await ctx.send(embed=embed, delete_after=60.0)


@bot.slash_command(name='id', description='Узнать id дискорд сервера, а также id его каналов')
async def id(ctx):
    ids_list = []
    for category in ctx.guild.categories:
        category_list = []
        category_list.append(f'**```{category.name}```**')
        category_list.append('`=============================================================`')
        for channel in category.text_channels:
            if ctx.author in channel.members:
                category_list.append(f'{channel.mention}  —  **`{channel.id}`**')
        if len(category_list) > 2:
            ids_list.append(category_list)
    main_embed = discord.Embed(title='**` СПИСОК ID `**',
                               description=f'`=============================================================`\n'
                                           f'**```ansi\n[2;34m ID сервера {ctx.guild.name}: [0m\n```**\n'
                                           f'`{ctx.guild.id}`\n'
                                           f'**```ansi\n[2;34m ID текущего канала: [0m\n```**\n'
                                           f'`{ctx.channel.id}`\n'
                                           f'**```ansi\n[2;34m ID всех текстовых каналов: [0m\n```**',
                               color=0x1e1f22)
    await ctx.respond(embed=main_embed)
    for short_ids_list in ids_list:
        embed = discord.Embed(title=short_ids_list[0],
                              description="\n".join(short_ids_list[1:]),
                              color=0x1e1f22)
        await ctx.send(embed=embed)


@bot.slash_command(name='stats', description='Просмотреть статистику пользователя')
async def stats(ctx, member: Option(discord.Member, description="Выберите пользователя: ", required=False)):
    if not member:
        member = ctx.author
    if member.raw_status in "dnd,idle,invisible,online":
        status = "В сети"
    else:
        status = "Не в сети"
    if member.activity:
        user_activity = member.activity.name
    else:
        user_activity = 'Отсутствует'
    embed = discord.Embed(title=f"Статистика пользователя", description=f"", color=0x1e1f22)
    embed.add_field(name="**`Статус:`**", value=f"{status}", inline=False)
    embed.add_field(name="**`Активность:`**", value=f"{user_activity}", inline=False)
    embed.add_field(name="**`Аккаунт создан:`**", value=f"{member.created_at.strftime('%Y.%m.%d - %H:%M')}",
                    inline=False)
    embed.add_field(name="**`Присоединился к серверу`**", value=f"{member.joined_at.strftime('%Y.%m.%d - %H:%M')}",
                    inline=False)
    embed.set_author(name=f"{member}", icon_url=member.avatar)
    embed.set_thumbnail(url=member.avatar)
    embed.set_footer(text=f'Статистика предоставлена по запросу {ctx.author}')
    await ctx.respond(embed=embed)


@bot.slash_command(name='serverinfo', description='Просмотреть статистику сервера, включая cross-server чаты')
async def serverinfo(ctx):
    guild_id = str(ctx.guild.id)
    tg_linked_channels = ['**```ansi\n[2;34m Каналы, связаныне с телеграм-группами [0m\n```**']
    ds_linked_channels = ['**```ansi\n[2;34m Каналы, связанные с дискорд-серверами [0m\n```**']
    if db.get(GUILDS, guild_id).LINKED_CHANNELS_ID:
        for channel in db.get(GUILDS, guild_id).LINKED_CHANNELS_ID.split(':'):
            channels = []
            for channel_id in db.get(LINKED, channel).LINKED_CHANNELS_ID.split(':'):
                channels.append(f"` {channel_id} ({bot.get_channel(int(channel_id)).guild.name})`")
            channels = "\n".join(channels)
            ds_linked_channels.append(f'<#{channel}>  —  **Привязанные каналы:**\n{channels}')
    else:
        ds_linked_channels.append('**` Отсутствуют. `**')
    if db.get(GUILDS, guild_id).TG_LINKED_CHANNELS_ID:
        for channel in db.get(GUILDS, guild_id).TG_LINKED_CHANNELS_ID.split(':'):
            tg_linked_channels.append(
                f'<#{channel}>  —  Id тг-группы: **`{db.get(TG_LINKED, channel).LINKED_CHANNEL_ID}`**')
    else:
        tg_linked_channels.append('**` Отсутствуют. `**')
    tg_linked_channels = "\n".join(tg_linked_channels)
    ds_linked_channels = "\n".join(ds_linked_channels)
    embed = discord.Embed(title=f"**` Статистика сервера `**",
                          description=f"**```ansi\n[2;34m {ctx.guild.name} [0m\n```**\n"
                                      f"**Id сервера**  —  `{ctx.guild.id}`\n"
                                      f"**Создан**  —  `{ctx.guild.created_at.strftime('%Y.%m.%d - %H:%M')}`\n"
                                      f"**Владелец**  —  <@{ctx.guild.owner_id}>\n\n"
                                      f"**Участников**  —  `{ctx.guild.member_count}`\n"
                                      f"**Каналов**  —  `{len(ctx.guild.channels)}`\n"
                                      f"**Ролей**  —  `{len(ctx.guild.roles)}`\n"
                                      f"**Бустов**  —  {ctx.guild.premium_subscription_count}\n\n"
                                      f"{tg_linked_channels}\n\n"
                                      f"{ds_linked_channels}",
                          color=0x1e1f22)
    embed.set_thumbnail(url=ctx.guild.icon.url)
    await ctx.respond(embed=embed)
    # for channels in [tg_linked_channels, ds_linked_channels]:
    #     embed = discord.Embed(title=channels[0],
    #                           description="\n".join(channels[1:]),
    #                           color=0x1e1f22)
    #     await ctx.channel.send(embed=embed)


@bot.slash_command(name='weather', description='Узнать прогноз погоды в выбранном городе')
async def weather(ctx,
                  place: Option(str, description="Введите название города: ", required=True)):
    appid = 'ef526c997e6a909c2a978311053fe37e'
    try:
        limit = 5
        res = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={place}&limit={limit}&appid={appid}")
        data = res.json()
        lat = data[0]['lat']
        lon = data[0]['lon']
        res = requests.get(
            f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&lang=ru&appid={appid}")
        data = res.json()

        weather_forecast = []
        wind_deg_list = []
        temp_list = []
        wind_speed_list = []
        humidity_list = []
        weather_list = []
        date = data['list'][0]['dt_txt'].split()[0]
        for part in data['list']:
            if part['dt_txt'].split()[0] != date:
                wind_deg = int(mean(wind_deg_list))
                min_temp = round(min(temp_list))
                max_temp = round(max(temp_list))
                min_wind = round(min(wind_speed_list))
                max_wind = round(max(wind_speed_list))
                humidity = round(mean(humidity_list))
                weather = mode(weather_list)
                if wind_deg in range(338, 360) or wind_deg in range(0, 23):
                    wind = '⬆'
                elif wind_deg in range(23, 68):
                    wind = '↗'
                elif wind_deg in range(68, 113):
                    wind = '➡'
                elif wind_deg in range(113, 158):
                    wind = '↘'
                elif wind_deg in range(158, 203):
                    wind = '⬇'
                elif wind_deg in range(203, 248):
                    wind = '↙'
                elif wind_deg in range(248, 293):
                    wind = '⬅'
                elif wind_deg in range(293, 338):
                    wind = '↖'

                mounths = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентбря',
                           'октября', 'ноября', 'декабря']

                date = f"""```ansi\n[2;34m---===≡≡╠ {int(date.split("-")[2])} {mounths[int(date.split("-")[1]) - 1]} ╣≡≡===---[0m\n```"""

                weather_forecast.append(
                    f'{date}  `Погода:` **{weather}**\n  `Температура:` **от {min_temp} до {max_temp}°C**\n  `Ветер:` **`〔{wind}〕`** **от {min_wind} до {max_wind}м/с**\n  `Влажность:` **{humidity}%**')

                wind_deg_list = []
                temp_list = []
                wind_speed_list = []
                humidity_list = []
                weather_list = []
                date = part['dt_txt'].split()[0]

            temp = part['main']['temp']
            humidity = part['main']['humidity']
            description = part['weather'][0]['description']
            wind_speed = part['wind']['speed']
            wind_deg = int(part['wind']['deg'])

            temp_list.append(temp)
            humidity_list.append(humidity)
            weather_list.append(description)
            wind_speed_list.append(wind_speed)
            wind_deg_list.append(wind_deg)

        title = f"``` {place} ```\n` {round(lat, 6)} {round(lon, 6)} `\n"
        text = '\n'.join(weather_forecast)
        embed = discord.Embed(title=title, description=text, color=0x2b2d31)
        await ctx.respond(embed=embed)
        # await ctx.reply((f"```{city}\n{round(lat, 4)} {round(lon, 4)}\nпрогноз погоды на 5 дней:\n\n```" + '\n\n'.join(weather_forecast)))
    except Exception as e:
        print(e)
        embed = discord.Embed(title='**` ОШИБКА `**',
                              description='**Пожалуйста, введите корректное \nназвание города или страны**',
                              color=0xff0000)
        await ctx.respond(embed=embed, delete_after=15.0, ephemeral=True)


class link_channel_request(discord.ui.View):
    def __init__(self, *, timeout=1000000000000000000000):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Присоединиться", style=discord.ButtonStyle.green)
    async def green_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            modal = link_channel_request_modal(title="Присоединение к общему каналу")
            await interaction.response.send_modal(modal)
        else:
            embed = discord.Embed(title="**` ОШИБКА `**",
                                  description=f"**Вам необходимо обладать правами\n"
                                              f"администратора, чтобы сделать это!**",
                                  color=0xff0000)
            await interaction.response.send_message(embed=embed, view=None, delete_after=7.0, ephemeral=True)


class link_channel_request_modal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(label="Канал, который станет общим чатом",
                                           placeholder='Введите id канала'))

    async def callback(self, interaction: discord.Interaction):
        if ((self.children[0].value).strip()).isdigit() and \
                bot.get_channel(int(self.children[0].value.replace(" ", ""))) in interaction.guild.channels and \
                bot.get_channel(int(self.children[0].value.replace(" ", ""))) not in interaction.guild.voice_channels:
            channel = bot.get_channel(int(self.children[0].value.replace(" ", "")))
            embed = discord.Embed(title="` ПОДТВЕРДИТЕ ДЕЙСТВИЕ `",
                                  description=f"**Вы уверены, что хотите сделать канал\n\n"
                                              f"<#{channel.id}> общим чатом?**",
                                  color=0xff0000)
            embed.set_footer(text=f'id выбранного канала: |{channel.id}|\n{interaction.message.embeds[0].footer.text}')
            await interaction.response.send_message(embed=embed, view=is_link_channel_id_correct(), ephemeral=True,
                                                    delete_after=30.0)
        else:
            embed = discord.Embed(title="` НЕКОРРЕКТНОЕ ЗНАЧЕНИЕ Id КАНАЛА `",
                                  description=f"**Пожалуйста, проверьте правильность введённых даныых.**\n\n"
                                              f"`Пример id канала:`   1068566917461327912",
                                  color=0xff0000)
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=10.0)


class is_link_channel_id_correct(discord.ui.View):
    def __init__(self, *, timeout=1000000000000000000000):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Так точно! ✔", style=discord.ButtonStyle.green)
    async def green_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        another_guild_id = int(interaction.message.embeds[0].footer.text.split('|')[3])
        another_guild_object = db.get(GUILDS, str(another_guild_id))
        guild_object = db.get(GUILDS, str(interaction.guild.id))
        channel_id = interaction.message.embeds[0].footer.text.split('|')[1]
        if db.get(GUILDS, str(interaction.message.guild.id)).LINKED_CHANNELS_ID and \
                len(db.get(GUILDS, str(interaction.message.guild.id)).LINKED_CHANNELS_ID.split(':')) >= 3:
            embed = discord.Embed(title="**` ОШИБКА! `**",
                                  description=f"**` У вас уже есть 3 общих чата с другими серверами! `**\n"
                                              f"**Максимальное количество каналов для одного сервера,\n"
                                              f"связанных с другими дискорд серверами сотавляет __3 канала__.\n"
                                              f"Удалите один из 3 cross-server каналов,\n"
                                              f"если хотите привязать новый!**\n\n"
                                              f"__*(Информация о всех общих чатах: /serverinfo)*__",
                                  color=0xff0000)
            await interaction.response.edit_message(embed=embed, view=None)
            return
        if not db.get(GUILDS, str(another_guild_id)).LINK_WAITING_CHANNEL_ID:
            embed = discord.Embed(title="**` ОШИБКА `**",
                                  description=f"**Вы уже приняли запрос от ** ` {bot.get_guild(another_guild_id).name} `\n"
                                              f"**или время действия запроса истекло!**",
                                  color=0xff0000)
            await interaction.response.edit_message(embed=embed, view=None, delete_after=7.0)
            return

        if channel_id in [o.CHANNEL_ID for o in db.query(LINKED).all()]:
            embed = discord.Embed(title="**` ОШИБКА `**",
                                  description=f"**Канал уже слинкован с другой гильдией!\n"
                                              f"Пожалуйста, выберите другой канал или\n откажитесь от присоединения!**",
                                  color=0xff0000)
            await interaction.response.edit_message(embed=embed, view=None, delete_after=7.0)
            return
        if db.get(GUILDS, interaction.guild_id).TG_LINKED_CHANNELS_ID and \
                channel_id in db.get(GUILDS, interaction.guild_id).TG_LINKED_CHANNELS_ID.split(':'):
            embed = discord.Embed(title='**` ОШИБКА `**',
                                  description='Выбранный дискорд канал уже связан с телеграм группой!\n'
                                              'Выберите другой канал, или отвяжите телеграм-группу\n'
                                              'от канала с помощью команды `/unlink_telegram`!',
                                  color=0xff0000)
            await interaction.response.edit_message(embed=embed, delete_after=30.0, view=None)
            return

        if another_guild_object.LINKED_CHANNELS_ID:
            channels_list = (another_guild_object.LINKED_CHANNELS_ID).split(":")
            if another_guild_object.LINK_WAITING_CHANNEL_ID not in channels_list:
                channels_list.append(another_guild_object.LINK_WAITING_CHANNEL_ID)
            another_guild_object.LINKED_CHANNELS_ID = ":".join(channels_list)
        else:
            another_guild_object.LINKED_CHANNELS_ID = another_guild_object.LINK_WAITING_CHANNEL_ID
        db.add(another_guild_object)
        db.commit()

        if guild_object.LINKED_CHANNELS_ID:
            channels_list = guild_object.LINKED_CHANNELS_ID.split(":")
            if channel_id not in channels_list:
                channels_list.append(channel_id)
            guild_object.LINKED_CHANNELS_ID = ":".join(channels_list)
        else:
            guild_object.LINKED_CHANNELS_ID = channel_id
        db.add(guild_object)
        db.commit()

        if channel_id in [o.CHANNEL_ID for o in db.query(LINKED).all()]:
            pass
        else:
            if db.get(LINKED, another_guild_object.LINK_WAITING_CHANNEL_ID) and \
                    db.get(LINKED, another_guild_object.LINK_WAITING_CHANNEL_ID).LINKED_CHANNELS_ID:

                channels_list = db.get(LINKED, another_guild_object.LINK_WAITING_CHANNEL_ID).LINKED_CHANNELS_ID.split(
                    ":")
                if another_guild_object.LINK_WAITING_CHANNEL_ID not in channels_list:
                    channels_list.append(another_guild_object.LINK_WAITING_CHANNEL_ID)
                CHANNEL = LINKED(CHANNEL_ID=channel_id,
                                 LINKED_CHANNELS_ID=":".join(channels_list))
            else:
                CHANNEL = LINKED(CHANNEL_ID=channel_id,
                                 LINKED_CHANNELS_ID=another_guild_object.LINK_WAITING_CHANNEL_ID)
            db.add(CHANNEL)
            db.commit()

        if another_guild_object.LINK_WAITING_CHANNEL_ID in [o.CHANNEL_ID for o in db.query(LINKED).all()]:
            for channel_ in db.get(LINKED, another_guild_object.LINK_WAITING_CHANNEL_ID).LINKED_CHANNELS_ID.split(":"):
                o = db.get(LINKED, channel_)
                channels_list = o.LINKED_CHANNELS_ID.split(":")
                if channel_id not in channels_list:
                    channels_list.append(channel_id)
                o.LINKED_CHANNELS_ID = ":".join(channels_list)
                db.add(o)
                db.commit()
            o = db.get(LINKED, another_guild_object.LINK_WAITING_CHANNEL_ID)
            channels_list = o.LINKED_CHANNELS_ID.split(":")
            if channel_id not in channels_list:
                channels_list.append(channel_id)
            o.LINKED_CHANNELS_ID = ":".join(channels_list)
            db.add(o)
            db.commit()
        else:
            CHANNEL = LINKED(CHANNEL_ID=another_guild_object.LINK_WAITING_CHANNEL_ID,
                             LINKED_CHANNELS_ID=channel_id)
            db.add(CHANNEL)
            db.commit()

        db.add(another_guild_object)
        db.add(guild_object)
        another_guild_object.LINK_WAITING_CHANNEL_ID = None
        guild_object.LINK_WAITING_CHANNEL_ID = None
        db.commit()

        embed = discord.Embed(title="` УСПЕШНО! ✔ `",
                              description=f"**Присоединение к общему чату завершено!\n**",
                              color=0x00BF32)
        embed.set_footer(text=f'{interaction.message.embeds[0].footer.text}')
        await interaction.response.edit_message(embed=embed, view=None, delete_after=15.0)

    @discord.ui.button(label="Закрыть ❌", style=discord.ButtonStyle.green)
    async def red_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(title="` ЗАКРЫТИЕ `",
                              color=0xff0000)
        await interaction.response.edit_message(embed=embed, view=None, delete_after=0.0)


class Buttons_DELETE(discord.ui.View):
    def __init__(self, *, timeout=1000000000000000000000):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="❌ Удалить!", style=discord.ButtonStyle.red)
    async def red_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('Автоматическое удаление канала через несколько секунд.')
        await asyncio.sleep(7)
        await interaction.channel.delete()

    @discord.ui.button(label="❎ Отменить!", style=discord.ButtonStyle.green)
    async def green_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.message.delete()


class Buttons_unlink_telegram(discord.ui.View):
    def __init__(self, *, timeout=1000000000000000000000):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="❌ Отвязать!", style=discord.ButtonStyle.red)
    async def red_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        group_id = interaction.message.embeds[0].footer.text.split('|')[1]
        guild_id = str(interaction.message.guild.id)
        channel_id = db.get(GROUPS, group_id).LINKED_CHANNEL_ID

        guild_object = db.get(GUILDS, guild_id)
        if ':' in guild_object.TG_LINKED_CHANNELS_ID:
            channels_list = guild_object.TG_LINKED_CHANNELS_ID.split(":")
            if channel_id in channels_list:
                channels_list.remove(channel_id)
            guild_object.TG_LINKED_CHANNELS_ID = ":".join(channels_list)
        else:
            guild_object.TG_LINKED_CHANNELS_ID = None

        group_object = db.get(GROUPS, group_id)
        group_object.LINKED_CHANNEL_ID = None
        db.delete(db.get(TG_LINKED, group_id))
        db.delete(db.get(TG_LINKED, channel_id))
        db.delete(db.get(WEBHOOKS, channel_id))
        db.add(guild_object)
        db.add(group_object)
        db.commit()

        embed = discord.Embed(title="**` ОТВЯЗКА ЗАВЕРЕШНА УСПЕШНО `**",
                              description=f"**Отключение общего дискорд чата выполнено.**",
                              color=0x00BF32)
        await interaction.response.edit_message(embed=embed, view=None, delete_after=60.0)

    @discord.ui.button(label="❎ Отменить!", style=discord.ButtonStyle.green)
    async def green_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(title='**` УСПЕШНАЯ ОТМЕНА `**', description='Отключение общего чата отменено!',
                              color=0x00BF32)
        await interaction.response.edit_message(embed=embed, view=None, delete_after=0)


@bot.event
async def on_ready():
    global BOT_IS_READY
    activity = discord.Activity(type=discord.ActivityType.watching, name="/help")
    await bot.change_presence(activity=activity)

    BOT_IS_READY = True
    print('Discord-bot started successfully!')


@bot.event
async def on_guild_join(guild):
    if not db.get(GUILDS, str(guild.id)):
        GUILD = GUILDS(GUILD_ID=str(guild.id))
        db.add(GUILD)
        db.commit()
    print('бот стал членом гильдии:  ', guild.id)
    pass


@bot.event
async def on_guild_remove(guild):
    if db.get(GUILDS, str(guild.id)):
        GUILD = db.get(GUILDS, str(guild.id))
        if GUILD.LINKED_CHANNELS_ID:
            for channel in GUILD.LINKED_CHANNELS_ID.split(':'):
                if not bot.get_channel(int(channel)):
                    for linked_channel_id in db.get(LINKED, channel).LINKED_CHANNELS_ID.split(':'):
                        linked_channel = db.get(LINKED, linked_channel_id)
                        channels = linked_channel.LINKED_CHANNELS_ID.split(":")
                        channels.remove(channel)
                        linked_channel.LINKED_CHANNELS_ID = ":".join(channels)
                        if not linked_channel.LINKED_CHANNELS_ID:
                            db.delete(linked_channel)
                        else:
                            db.add(linked_channel)
                        db.commit()
                        for o in db.query(GUILDS).all():
                            if o.LINKED_CHANNELS_ID and linked_channel_id in o.LINKED_CHANNELS_ID:
                                if not db.get(LINKED, linked_channel_id):
                                    channels = o.LINKED_CHANNELS_ID.split(":")
                                    channels.remove(linked_channel_id)
                                    o.LINKED_CHANNELS_ID = ":".join(channels)
                                    if not o.LINKED_CHANNELS_ID:
                                        o.LINKED_CHANNELS_ID = None
                                    db.add(o)
                                    db.commit()
                            if o.LINKED_CHANNELS_ID and channel in o.LINKED_CHANNELS_ID:
                                channels = o.LINKED_CHANNELS_ID.split(":")
                                channels.remove(channel)
                                o.LINKED_CHANNELS_ID = ":".join(channels)
                                if not o.LINKED_CHANNELS_ID:
                                    o.LINKED_CHANNELS_ID = None
                                db.add(o)
                                db.commit()
                    db.delete(db.get(LINKED, channel))
                    db.commit()
        if GUILD.TG_LINKED_CHANNELS_ID:
            for channel in db.get(GUILDS, str(guild.id)).TG_LINKED_CHANNELS_ID.split(':'):
                if db.get(WEBHOOKS, channel):
                    db.delete(db.get(WEBHOOKS, channel))
                if db.get(TG_LINKED, channel):
                    group_object = db.get(GROUPS, (db.get(TG_LINKED, channel).LINKED_CHANNEL_ID))
                    group_object.LINKED_CHANNEL_ID = None
                    db.add(group_object)
                    db.delete(db.get(TG_LINKED, (db.get(TG_LINKED, channel).LINKED_CHANNEL_ID)))
                    db.delete(db.get(TG_LINKED, channel))
                db.commit()
        db.delete(GUILD)
        db.commit()

    print('бот покинул гильдию:  ', guild.id)
    pass


bot.run(DS_TOKEN)

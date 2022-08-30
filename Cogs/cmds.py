import discord, aiohttp, datetime, os, asyncio, random, traceback, io, magic, re, time, pandas
from discord.ext import commands
from contextlib import suppress
from Config.utils import yt_search, ACRcloud, HerokuRecognizer
from typing import List
from discord.ext.commands import has_permissions
from Config.components import SetInfo, ViolaEmbed, OnSettings
from Config.utils import Paginator
from discord import app_commands
from Config.core import Viola
from discord.http import Route
# -----------------------------------------------------------------------------------------------------------
class cmds(commands.Cog, description='**Основные команды бота.**'):
    def __init__(self, bot: Viola):
        self.bot = bot
    async def cog_load(self):
        self.uptime = time.time()
    @commands.command()
    async def whatsit(self, ctx: commands.Context):
        async with ctx.channel.typing():
            if len(ctx.message.attachments) > 1:
                return await ctx.message.reply('`Вы можете прикрепить только один файл.`')
            elif len(ctx.message.attachments) == 0:
                return await ctx.message.reply('`Вам нужно прикрепить файл.`')
            with io.BytesIO(await ctx.message.attachments[0].read()) as data:
                typo = await self.bot.loop.run_in_executor(None, magic.from_buffer, data.read())
            name = ctx.message.attachments[0].filename
            embed = ViolaEmbed(ctx=ctx)
            embed.description = f'`{name} Имеет следующую сигнатуру:`\n\n>>> ---\n**{typo}**\n---'
            await ctx.message.reply(embed=embed)
        
    @commands.command(description="Прикрепите отрывок песни или целую песню, введите эту команду и бот попытается угадать ее название, исполнителя и показать ютуб статистику.")
    async def recognize(self, ctx: commands.Context):
        async with ctx.channel.typing():
            try:
                if len(ctx.message.attachments) > 1:
                    return await ctx.message.reply('`Вы можете прикрепить только один файл.`')
                elif len(ctx.message.attachments) == 0:
                    return await ctx.message.reply('`Вам нужно прикрепить файл.`')
                embed=ViolaEmbed(ctx=ctx, format='warning')
                embed.description = 'Ожидайте...\n*Процесс может занять до 30 секунд...*'
                embed.set_author(name=f'{ctx.message.attachments[0].filename}', url='https://cdn.discordapp.com/emojis/1010919398044872725.gif?size=128&quality=lossless')
                mess = await ctx.channel.send(embed=embed)
                a = await ctx.message.attachments[0].read()
                with io.BytesIO(a) as audio_data:
                    accepted = ['Audio file with ID3', 'Ogg data', 'WAVE audio', 'MPEG ADTS']
                    typo = await self.bot.loop.run_in_executor(None, magic.from_buffer, audio_data.read())
                    if not (accepted[0] in typo or accepted[1] in typo or accepted[2] in typo or accepted[3] in typo):
                        embed = ViolaEmbed(ctx=ctx, format='error')
                        embed.description = f'`Формат файла не поддерживается.`\n(**{typo}**)\n`Поддерживаемые файлы: .ogg .wav .mp3 .adts`'
                        try:
                            await mess.edit(embed=embed)
                        except discord.errors.NotFound:
                            await ctx.channel.send(embed=embed)
                        return
                with io.BytesIO(a) as audio_data:
                    # song = await ACRcloud().recognize(audio_bytes=audio_data.read(2**20))
                    executor = HerokuRecognizer()
                    song = await executor.recognize_API(music_bytes=audio_data.read(2**20))
                    if not song:
                        embed = ViolaEmbed(ctx=ctx, format='error')
                        embed.description = '`Совпадений для выбранного фрагмента не найдено.`'
                        try:
                            return await mess.edit(embed=embed)
                        except discord.errors.NotFound:
                            return await ctx.channel.send(embed=embed)
                    yt = await yt_search(f'{song.title} - {song.author}')
                    embed = ViolaEmbed(ctx=ctx)
                    embed.set_thumbnail(url=song.thumbnail_url)
                    description = f'`Найдено совпадение:`\n`Название:` **{song.title}**\n`Исполнитель:` **{song.author}**'
                    description += f'\n\n**YT search:**\n`Ссылка на видео:` [{yt.title}](https://www.youtube.com/watch?v={yt.identifier})\n`Ссылка на канал:` [{yt.author}]({yt.author_url})\n`Длительность:` {yt.duration}\n`Просмотры:` {yt.view_count}'
                    embed.description = description
                    try:
                        return await mess.edit(embed=embed)
                    except discord.errors.NotFound:
                        return await ctx.channel.send(embed=embed)
            except Exception as e:
                embed = ViolaEmbed(ctx=ctx, format='error')
                embed.description = f'`{e if isinstance(e, str) and e != "" else "undefined error happened..."}`\n**{e.__class__.__name__}**'
                await mess.edit(embed=embed)

    @commands.command(description="Вспомогательная утилита.\nУдаляет дискорд вебхуки.\nПример: `s!webhookdel https://discord.com/api/webhooks/\n1007626877843812362/j_O-_9JiaC7JTiAquW15\nvZb8PaO0mLlujEplsgwVnM3710O\nUBEePhToo1c-UJVcnvpcV`")
    async def webhookdel(self, ctx: commands.Context, url):
        async with ctx.channel.typing():
            m = re.search(r'discord(?:app)?.com/api/webhooks/(?P<id>[0-9]{17,20})/(?P<token>[A-Za-z0-9\.\-\_]{60,68})', url)
            if m is None:
                return await ctx.message.reply('`Укажите достоверный url вебхука.`')
            async with self.bot.session.delete(url) as response:
                await ctx.message.reply(f'`Действие выполнено со статусом` **{response.status}**')
    
    @commands.command(description="Команда.\nУзнайте топ сервера по голосовой активности и по опыту.\nПример: `s!top voice` топ сервера по голосу.")
    async def top(self, ctx: commands.Context, *category):
        async with ctx.channel.typing():
            if not category:
                # embeds = [discord.Embed(color=discord.Color.red(), description='1'), discord.Embed(color=discord.Color.green(), description='2'), discord.Embed(color=discord.Color.blurple(), description='3')]
                embeds: List[discord.Embed] = []
                try:
                    buffer = []
                    res = await self.bot.bd.fetch({'guildid': ctx.guild.id}, mode='all', category='messages')
                    for x in res.value:
                        buffer.append({'memberid': x['memberid'], 'amount': x['amount']})
                    buffer = sorted(buffer, key = lambda x: x['amount'])
                    buffer = buffer[::-1]
                    embed = discord.Embed(color=discord.Color.green())
                    embed.title = f'Топ сервера {ctx.guild.name} по сообщениям.✍️'
                    description = ''
                    count = 0
                    # --------------------------
                    for i in buffer:
                        count += 1
                        if count % 6 == 0:
                            embed.description = description
                            embeds.append(embed)
                            embed = discord.Embed(color=discord.Color.green())
                            embed.title = f'Топ сервера {ctx.guild.name} по сообщениям.✍️'
                            embed.description = ''
                            description = ''
                        try:
                            member = ctx.guild.get_member(int(i['memberid']))
                        except:
                            member = await self.bot.fetch_user(int(i['memberid']))
                            try:
                                memberi = f'{member.name}#{member.discriminator} (Вышел)'
                            except AttributeError:
                                memberi = f'<@!{int(i["memberid"])}> (Вышел)'
                            level = self.bot.format_level(i['amount'])
                            description += f'**#{count}.** `{memberi}`\n`Уровень:` **{level[0]}** | `Опыт:` **({i["amount"]*3}/{level[1]*3})**\n\n'
                            continue
                        level = self.bot.format_level(i['amount'])
                        if member is not None:
                            description += f'**#{count}.** **{member.nick if member.nick else member.name}**\n`Уровень:` **{level[0]}** | `Опыт:` **({i["amount"]*3}/{level[1]*3})**\n\n'
                        else:
                            description += f'**#{count}.** `<@!{int(i["memberid"])}> (Вышел)`\n`Уровень:` **{level[0]}** | `Опыт:` **({i["amount"]*3}/{level[1]*3})**\n\n'
                    embed.description = description
                    embeds.append(embed)
                    if len(embeds) > 1:
                        await ctx.send('⚠️Показывается статистика в момент вызова команды.', embed=embeds[0], view=Paginator(embeds=embeds, ctx=ctx, bot=self.bot))
                    else:
                        await ctx.send('⚠️Показывается статистика в момент вызова команды.', embed=embeds[0])
                except Exception:
                    print(traceback.format_exc())
                return
            if category[0] == 'voice':
                embeds: List[discord.Embed] = []
                try:
                    buffer = []
                    res = await self.bot.bd.fetch({'guildid': ctx.guild.id}, mode='all', category='voice')
                    for x in res.value:
                        buffer.append({'memberid': x['memberid'], 'amount': x['amount']})
                    buffer = sorted(buffer, key = lambda x: x['amount'])
                    buffer = buffer[::-1]
                    embed = discord.Embed(color=discord.Color.green())
                    embed.title = f'Топ сервера {ctx.guild.name} по голосу.🎙️'
                    description = ''
                    count = 0
                    # --------------------------
                    buffer2 = []
                    res = await self.bot.bd.fetch({'guildid': ctx.guild.id}, mode='all', category='messages')
                    if res.status:
                        for x in res.value:
                            buffer2.append({'memberid': x['memberid'], 'amount': x['amount']})
                    # --------------------------
                    for i in buffer:
                        if int(i['amount']) == 0:
                            continue
                        count += 1
                        if count % 6 == 0:
                            embed.description = description
                            embeds.append(embed)
                            embed = discord.Embed(color=discord.Color.green())
                            embed.title = f'Топ сервера {ctx.guild.name} по голосу.🎙️'
                            embed.description = ''
                            description = ''
                        try:
                            member = ctx.guild.get_member(int(i['memberid']))
                        except:
                            member = None
                        if member is None:
                            member = await self.bot.fetch_user(int(i['memberid']))
                            try:
                                memberi = f'{member.name}#{member.discriminator} (Вышел)'
                            except AttributeError:
                                memberi = f'<@!{int(i["memberid"])}> (Вышел)'
                            description += f'**#{count}.** `{memberi}`\n`Время:` **{self.bot.format_time(i["amount"])}**\n'
                            done = False
                            for y in buffer2:
                                if i['memberid'] == y['memberid']:
                                    level = self.bot.format_level(y['amount'])
                                    description += f'`Уровень:` **{level[0]}** | `Опыт:` **({y["amount"]*3}/{level[1]*3})**\n\n'
                                    done = True
                            if not done:
                                description += f'`Уровень:` **0** | `Опыт:` **(0/30)**\n\n'
                        else:
                            description += f'**#{count}** **{member.nick if member.nick else member.name}**\n`Время:` **{self.bot.format_time(i["amount"])}**\n'
                            done = False
                            for y in buffer2:
                                if i['memberid'] == y['memberid']:
                                    level = self.bot.format_level(y['amount'])
                                    description += f'`Уровень:` **{level[0]}** | `Опыт:` **({y["amount"]*3}/{level[1]*3})**\n\n'
                                    done = True
                            if not done:
                                description += f'`Уровень:` **0** | `Опыт:` **(0/30)**\n\n'
                    embed.description = description
                    embeds.append(embed)
                    for i, embed in enumerate(embeds):
                        try:
                            embed.set_footer(text=f'{ctx.guild.name} Страница {i+1}/{len(embeds)}', icon_url=f'{ctx.guild.icon.url}')
                        except Exception:
                            embed.set_footer(text=f'{ctx.guild.name} Страница {i+1}/{len(embeds)}', icon_url=f'{self.bot.user.avatar.url}')
                    if len(embeds) > 1:
                        await ctx.send('⚠️Показывается статистика в момент вызова команды.', embed=embeds[0], view=Paginator(embeds=embeds, ctx=ctx, bot=self.bot))
                    else:
                        await ctx.send('⚠️Показывается статистика в момент вызова команды.', embed=embeds[0])
                except Exception:
                    print(traceback.format_exc())
    
    @commands.command(description='Благодаря этой команде вы можете вступить в брак с кем нибудь!\nПример: `s!marry @партнер`')
    async def marry(self, ctx: commands.Context, member: discord.Member = None):
        if member is None:
            await ctx.message.reply('`Вам необходимо указать цель.`')
            return
        if member.bot:
            await ctx.message.reply('`На ботах жениться нельзя!`')
            return
        if member == ctx.author:
            await ctx.message.reply('`Попробуйте жениться на ком нибудь другом.`')
            return
        res = await self.bot.bd.fetch({'memberid': ctx.author.id, 'guildid': ctx.author.id}, category='marry')
        if not res.status:
            res = await self.bot.bd.fetch({'partnerid': ctx.author.id, 'guildid': ctx.author.id}, category='marry')
            if res.status:
                await ctx.channel.send('`Вы уже женаты/замужем.`')
                return
        else:
            await ctx.channel.send('`Вы уже женаты/замужем.`')
            return
        res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'memberid': member.id}, category='marry')
        if not res.status:
            res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'partnerid': member.id}, category='marry')
        if res.status:
            if int(res.value['memberid']) == int(member.id):
                second = int(res.value['partnerid'])
            else:
                second = int(res.value['memberid'])
            await ctx.message.reply(f'>>> Этот человек уже находится в браке с {self.bot.get_user(int(second))}\nСвадьба была <t:{int(res.value["date"])}:R>')
            return
        def check(reaction, user):
            return user == member and (reaction.emoji == '✅' or reaction.emoji == '❌')
        embed = discord.Embed(color=discord.Colour.brand_red())
        embed.title = 'Свадьба.💞'
        embed.description = f'**{ctx.author.name}#{ctx.author.discriminator} Предлагает вам свадьбу.🥰\nУ вас есть 5 минут на принятие решения.**'
        mess = await ctx.channel.send(f'{member.mention} Минуточку внимания...', embed=embed)
        async def a1(mess: discord.Message):
            await mess.add_reaction('✅')
        async def a2(mess: discord.Message):
            await mess.add_reaction('❌')
        self.bot.loop.create_task(a1(mess))
        self.bot.loop.create_task(a2(mess))
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=300.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(color=discord.Color.brand_red())
            embed.title = 'Свадьбы не будет.💔'
            embed.description = f'**Свадьба отменяется, так как у {member.name}#{member.discriminator} закончилось время...\nА начиналось так красиво...**'
            try:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{ctx.author.guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
            await mess.edit(embed=embed)
            await mess.clear_reactions()
            return
        if reaction.emoji == '❌':
            embed = discord.Embed(color=discord.Colour.brand_red())
            embed.title = 'Свадьба Отменяется.💔'
            embed.description = f'**Свадьбы не будет так как {member.name}#{member.discriminator} отказал(а) {ctx.author.name}#{ctx.author.discriminator}**'
            try:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{ctx.author.guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
            await ctx.channel.send(embed=embed)
            await mess.clear_reactions()
        elif reaction.emoji == '✅':
            res = await self.bot.bd.fetch({'memberid': ctx.author.id, 'guildid': ctx.author.id}, category='marry')
            if not res.status:
                res = await self.bot.bd.fetch({'partnerid': ctx.author.id, 'guildid': ctx.author.id}, category='marry')
                if res.status:
                    await ctx.channel.send('`Вы уже женаты/замужем.`')
                    return
            else:
                await ctx.channel.send('`Вы уже женаты/замужем.`')
                return
            embed = discord.Embed(color=discord.Colour.brand_red())
            embed.title = 'Свадьба.💞'
            embed.description = f'**Ура! С этого дня {member.name}#{member.discriminator} и {ctx.author.name}#{ctx.author.discriminator} находятся в браке! Горько!**'
            await self.bot.bd.add({'guildid': ctx.guild.id, 'memberid': member.id, 'partnerid': ctx.author.id, 'date': int(datetime.datetime.now().timestamp())}, category='marry')
            try:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{ctx.author.guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
            await ctx.channel.send(embed=embed)
            try:
                await mess.delete()
            except discord.errors.NotFound:
                pass
    
    @commands.command(description='Если вам надоела ваша вторая половинка, вы можете развестись с ней.')
    async def divorce(self, ctx: commands.Context) -> None:
        res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'partnerid': ctx.author.id}, category='marry')
        if not res.status:
            res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'memberid': ctx.author.id}, category='marry')
            if not res.status:
                await ctx.message.reply('`Сначала женитесь с кем то что-бы развестись!`')
                return
        def check(reaction, user):
            return user == ctx.author and reaction.emoji == '💔'
        if int(res.value['memberid']) == int(ctx.author.id):
            second = int(res.value['partnerid'])
        else:
            second = int(res.value['memberid'])
        embed = discord.Embed(color=discord.Color.brand_red())
        embed.title = 'Стоп стоп стоп'
        embed.description = f'**Вы уверены что хотите развестить с {self.bot.get_user(int(second))}?**💔'
        try:
            embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{ctx.author.guild.icon.url}')
        except Exception:
            embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
        mess = await ctx.channel.send(embed=embed)
        await mess.add_reaction('💔')
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            await self.bot.bd.remove(res.value, category='marry')
            try:
                await mess.delete()
            except discord.errors.NotFound:
                pass
            embed = discord.Embed(color=discord.Color.brand_red())
            embed.title = 'Развод состоялся💔'
            embed.description = f'**Вы успешно развелись с {self.bot.get_user(int(second))}**\n**Ваш брак был зарегистрирован:** <t:{int(res.value["date"])}:R>'
            try:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{ctx.author.guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
            mess = await ctx.channel.send(embed=embed)
        except asyncio.TimeoutError:
            await mess.delete()
            return
    
    @commands.command(description="Вспомогательная команда.\nБлагодаря этой команде вы можете обнулить уровень любого человека.")
    @has_permissions(administrator=True)
    async def resetlevel(self, ctx: commands.Context, member: discord.Member = None) -> None:
        if ctx.message.reference:
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = msg.author
        else:
            if member is None:
                member = ctx.author
        res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'memberid': member.id}, category='messages')
        res2 = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'memberid': member.id}, category='voice')
        if res.status or res2.status:
            embed = discord.Embed(color=discord.Color.brand_red())
            embed.title = 'Внимание!'
            embed.description = f'Обнулить статистику {member.mention}?'
            mess = await ctx.channel.send(embed=embed)
            async def a1(mess: discord.Message):
                await mess.add_reaction('✅')
            async def a2(mess: discord.Message):
                await mess.add_reaction('❌')
            self.bot.loop.create_task(a1(mess))
            self.bot.loop.create_task(a2(mess))
            def check(reaction, user):
                return user == ctx.author and (reaction.emoji == '✅' or reaction.emoji == '❌')
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await mess.delete()
                return
            if reaction.emoji == '✅':
                await self.bot.bd.remove({'guildid': ctx.guild.id, 'memberid': member.id}, category='messages')
                await self.bot.bd.remove({'guildid': ctx.guild.id, 'memberid': member.id}, category='voice')
                await mess.edit(embed=discord.Embed(color=discord.Color.brand_red(), title='Успешно.', description=f'Статистика сервера у {member.mention} обнулена.'))
                await mess.clear_reactions()
            elif reaction.emoji == '❌':
                await mess.delete()
        elif not res.status and not res2.status:
            embed = discord.Embed(color=discord.Color.brand_red())
            embed.title = 'Ошибка'
            embed.description = f'{member.mention} имеет нулевую статистику на сервере.'
            mess = await ctx.channel.send(embed=embed)
    
    @commands.command(aliases=['user-info'], description='Утилита.\nС помощью этой команды вы можете посмотреть подробную информацию об участнике сервера.')
    async def user(self, ctx: commands.Context, member: discord.Member=None) -> None:
        try:
            async with ctx.channel.typing():
                if ctx.message.reference:
                    msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                    member = msg.author
                else:
                    if member is None:
                        member = ctx.author
                if member.avatar:
                    url = member.avatar.url
                else:
                    url = self.bot.user.avatar.url
                embed = discord.Embed(color=member.top_role.color)
                description = f'{member.mention}\n(Заполнить информацию о себе: `s!setinfo`)\n\n'
                # -------------
                if not member.bot:
                    res = await self.bot.bd.fetch({'memberid': member.id, 'guildid': ctx.guild.id}, category='bio')
                    if res.status:
                        description += f'`Био:`\n```{res.value["data"]}```\n'
                    else:
                        description += f'`Био:`\n ```Не указано.```\n'
                    # -------------
                    res = await self.bot.bd.fetch({'memberid': member.id, 'guildid': ctx.guild.id}, category='age')
                    if res.status:
                        description += f'>>> `Возраст:` {res.value["data"]}\n'
                    else:
                        description += f'>>> `Возраст:` Не указан.\n'
                    # -------------
                    res = await self.bot.bd.fetch({'memberid': member.id, 'guildid': ctx.guild.id}, category='gender')
                    if res.status:
                        description += f'`Пол:` {res.value["data"]}\n'
                    else:
                        description += f'`Пол:` Не указан.\n'
                    # -------------
                    res = await self.bot.bd.fetch({'memberid': member.id, 'guildid': ctx.guild.id}, category='name')
                    if res.status:
                        description += f'`Имя:` {res.value["data"]}\n\n'
                    else:
                        description += f'`Имя:` Не указано.\n\n'
                    # -------------
                    res = await self.bot.bd.fetch({'guildid': member.guild.id, 'memberid': member.id}, category='messages')
                    if res.status:
                        level = self.bot.format_level(res.value['amount'])
                        description += f'`Уровень:` **{level[0]}** `({res.value["amount"]*3}/{level[1]*3})`\n'
                    else:
                        description += f'`Уровень:` **0** `(Не написано ни одного сообщения)`\n'
                    # ---------------------------------------------
                    res = await self.bot.bd.fetch({'guildid': member.guild.id, 'memberid': member.id}, category='voice')
                    if res.status:
                        tim = self.bot.format_time(res.value['amount'])
                        description += f'`Времени в голосовых каналах:` **{tim}**\n\n'
                    else:
                        description += f'`Времени в голосовых каналах:` **0:00**\n\n'
                    # --------------------------------------------- 
                    args = await self.bot.get_marry_info(member)
                    if args is not None:
                        description += f'`Брак:` В браке с **{self.bot.get_user(args["partner"])}**\n`Дата свадьбы:` <t:{args["date"]}:R>\n\n'
                    else:
                        description += f'`Брак:` Не состоит в браке.\n\n'
                # ---------------------------------------------
                description += f'`Аватар` [[Клик]]({url})\n'
                embed.title = f'Информация о {member.name}'
                if member.nick is not None:
                    description += f'`Пользовательский ник:` **{member.nick}**\n'
                description += f'`Аккаунт создан:` <t:{int(member.created_at.timestamp())}:R>\n'
                res = await self.bot.bd.fetch({'guildid': member.guild.id, 'memberid': member.id}, category='joined')
                if not res.status:
                    description += f'`Присоединился к серверу:` <t:{int(member.joined_at.timestamp())}:R>\n'
                else:
                    description += f'`Впервые присоединился к серверу:` <t:{res.value["time"]}:R>\n'
                animated = False
                if member.avatar:
                    if member.avatar.is_animated():
                        animated = True
                # we need to fetch banner
                banner = await self.bot.http.request(Route('GET', f'/users/{member.id}'))
                banner = banner['banner']
                description += '`Имеет премиум подписку.`<:nitro:1009420900535386122>\n' if member.premium_since or animated or banner else ""
                if member.activity is not None:
                    if member.activity.type is discord.ActivityType.playing:
                        description += f'`Играет в` **{member.activity.name}**'
                    elif member.activity.type is discord.ActivityType.streaming:
                        description += f'`Стримит` **{member.activity.name}**'
                    elif member.activity.type is discord.ActivityType.listening:
                        description += f'`Слушает` **{member.activity.name}**'
                    elif member.activity.type is discord.ActivityType.watching:
                        description += f'`Смотрит` **{member.activity.name}**'
                    elif member.activity.type is discord.ActivityType.competing:
                        description += f'`Соревнуется` **{member.activity.name}**'
                    else:
                        description += f'`Пользовательский статус:` **{member.activity.name if member.activity.name != None else "Отсутствует."}**'
                    description += '\n'
                if member.status is discord.Status.offline:
                    description += f'`Статус:` <:offline:1004822660481548368> Не в сети.'
                elif member.status is discord.Status.online:
                    if member.is_on_mobile():
                        description += f'`Статус:` <:online:1004825002203426856> В сети.'
                    else:
                        description += f'`Статус:` <:online:1004822664269008976> В сети.'
                elif member.status is discord.Status.dnd or member.status is discord.Status.do_not_disturb:
                    description += f'`Статус:` <:dnd:1004822667817406496> Не беспокоить.'
                elif member.status is discord.Status.idle:
                    description += f'`Статус:` <:idle:1004822662629040208> Не активен.'
                description += '\n'
                if member.is_timed_out():
                    description+=f'`Находится в тайм-ауте до:` <t:{member.timed_out_until.timestamp()}:R>\n'
                description += f'`Самая высокая роль:` <@&{member.top_role.id}>'
                embed.description = description
                embed.set_thumbnail(url=url)
                try:
                    embed.set_footer(text=f'{member.guild.name}', icon_url=f'{member.guild.icon.url}')
                except Exception:
                    embed.set_footer(text=f'{member.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
                await ctx.channel.send(embed=embed)
        except Exception:
            print(traceback.format_exc())

    @commands.command(description="Утилита.\nРасскажите о себе. Эта информация появится на вашем профиле на сервере.")
    async def setinfo(self, ctx: commands.Context) -> None:
        async with ctx.channel.typing():
            embed = ViolaEmbed(ctx=ctx)
            embed.description = '>>> Выберите действие,\nКоторое вам нужно:'
            view = SetInfo(ctx=ctx)
            view.message = await ctx.channel.send(embed=embed, view=view)
    
    @commands.command(description="Отключает команду на этом сервере. Пример: `s!disable marry`\n(с отключенными командами нельзя взаимодействовать.)")
    @has_permissions(administrator=True)
    async def disable(self, ctx: commands.Context, command) -> None:
        if command == 'disable' or command == 'enable':
            return await ctx.message.reply('Вы не можете отключать эти команды!')
        if command == 'levelling':
            res = await self.bot.bd.fetch({'guildid': ctx.guild.id}, category='levelling')
            if not res.status:
                await self.bot.bd.add({'guildid': ctx.guild.id}, category='levelling')
                return await ctx.send('`Оповещения о повышении уровней отключены.`')
            else:
                return await ctx.send('`Эта функция уже отключена.`')
        for x in self.bot.commands:
            if str(x.name) == str(command):
                res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'commandname': str(x.name)}, category='disabledcmds')
                if res.status:
                    await ctx.message.reply('`Команда уже отключена. Нет смысла снова ее отключать.✅`')
                else:
                    await self.bot.bd.add({'guildid': ctx.guild.id, 'commandname': str(x.name)}, category='disabledcmds')
                    await ctx.message.reply(f'`Команда {command} отключена.✅`\n`Используйте s!enable чтобы включить ее.`')
    
    @commands.command(description='Если команда была отключена, то включает ее назад. (с отключенными командами взаимодействовать нельзя)')
    @has_permissions(administrator=True)
    async def enable(self, ctx: commands.Context, command) -> None:
        if command == 'levelling':
            res = await self.bot.bd.fetch({'guildid': ctx.guild.id}, category='levelling')
            if res.status:
                await self.bot.bd.remove({'guildid': ctx.guild.id}, category='levelling')
                return await ctx.send('`Оповещения о повышении уровней включены.`')
            else:
                return await ctx.send('`Эта функция не отключена.`')
        for x in self.bot.commands:
            if str(x.name) == str(command):
                res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'commandname': str(x.name)}, category='disabledcmds')
                if not res.status:
                    await ctx.message.reply('`Команда не отключена.`')
                else:
                    await self.bot.bd.remove({'guildid': ctx.guild.id, 'commandname': str(x.name)}, category='disabledcmds')
                    await ctx.message.reply(f'`Команда {command} включена обратно.✅`')

    @app_commands.command(description="Задержка бота в миллисекундах.")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking= True)
        ping1 = f"{str(round(self.bot.latency * 1000))}ms"
        embed = discord.Embed(title = "**Pong!**", color = 0xafdafc)
        tim = time.time()
        await self.bot.bd.fetch({}, category='system')
        secs = round((time.time() - tim)*1000)
        embed.description = f'`Обработка команд:` **{ping1}**\n`База данных:` **{secs}ms**\n`кол-во операций с бд:` **{self.bot.bd.operations}**\n`Время работы:` **{self.bot.format_time(round(time.time()-self.uptime))}**'
        await interaction.followup.send(embed = embed)

    @commands.command(description = 'Утилита.\nУзнайте аватар любого пользователя.')
    async def avatar(self, ctx: commands.Context, user: discord.User = None) -> None:
        if user is None:
            user = ctx.author
        embed = ViolaEmbed(ctx=ctx)
        embed.description = f'`Аватар Пользователя` **{user}**'
        embed.set_thumbnail(url=None)
        try:
            embed.set_image(url=user.avatar.url)
            await ctx.send(embed = embed)
        except Exception:
            await ctx.message.reply('`У пользователя нет аватара.`')
    
    @has_permissions(administrator=True)
    @commands.command(description="Очистка чата.\nПараметры: лимит и (опционально) пользователь.\nУдаляет (лимит) сообщений и если указан пользователь, то удаляет сообщения от конкретного пользователя.")
    async def purge(self, ctx: commands.Context, limit: str, member: discord.Member = None) -> None:
        if not member:
            if int(limit) > 1000:
                return await ctx.message.reply('`Лимит сообщений не может быть больше 1000.`')
            deleted = await ctx.channel.purge(limit=int(limit))
            await ctx.channel.send(f'Удалено {len(deleted)} сообщений.')
        else:
            deleted = await ctx.channel.purge(limit=int(limit), check=lambda m: m.author == member)
            await ctx.channel.send(f'Удалено {len(deleted)} сообщений от пользователя <@!{member.id}>')
    
    @commands.command(description='Узнайте совместимость обсолютно любых двух вещей.\nПример: `s!ship Вася Петя`')
    async def ship(self, ctx: commands.Context, *args) -> None:
        if not args or len(args) != 2:
            await ctx.send('`s!ship <name1> <name2>`')
            return
        name = args[0]
        name2 = args[1]
        if len(name) == 21:
            name = str(name).replace('<@', '').replace('>', '')
            name = self.bot.get_user(int(name)).name
        if len(name2) == 21:
            name2 = str(name2).replace('<@', '').replace('>', '')
            name2 = self.bot.get_user(int(name2)).name
        if str(name2[:len(name2)//2]) == str(name2[len(name2)//2:]):
            temp1 = str(name2[:len(name2)//2])
        shipname = name[:len(name)//2] + (str(name2).replace(str(name2[:len(name2)//2]), '') + temp1 if temp1 is not None else None)
        compatibility = random.randint(1, 99)
        string = list('▬▬▬▬▬▬▬▬▬▬')
        string[compatibility // 10] = ':heart:'
        string = "[" + ''.join(string) + "]"
        embed = discord.Embed(title=f'Сравниваемые имена: {name} и {name2}.', description=f'Имечко: **{shipname}**\nСовместимость: **{compatibility}**% :heart:\n**{string}**')
        embed.color = discord.Color.random()
        await ctx.send(embed=embed)

    @commands.command(description='Скажите любое сообщение от имени бота.\nПример: `s!say hello`')
    async def say(self, ctx: commands.Context, *content) -> None:
        async def d1(ctx: commands.Context):
            await ctx.message.delete()
        async def s2(ctx: commands.Context, content):
            await ctx.send(' '.join(content))
        if not content:
            await ctx.message.delete()
            return
        self.bot.loop.create_task(d1(ctx))
        self.bot.loop.create_task(s2(ctx, content))

    @commands.command(aliases = ['guilds', ], description ='Этой командой может пользоваться только мой владелец.')
    async def leave(self, ctx: commands.Context, *guildid) -> None:
        if ctx.author.id == self.bot.owner_id:
            if not guildid:
                msg = ''
                for i in self.bot.guilds:
                    msg += f'`{i}, {i.id}`\n'
                await ctx.send(embed = discord.Embed(title='Мои Сервера: ',description=msg, color=0x00ffff))
                return
            guildid = int(guildid[0])
            try:
                guild = self.bot.get_guild(guildid)
                if guild is not None:
                    await guild.leave()
                    await ctx.send(f"`Я покинула {guild.name}`")
                else:
                    await ctx.send("`Сервер не найден.`")
            except:
                await ctx.send("`Что то пошло не так...`")

    @commands.command(description="Заглушает всех людей в голосовом канале. Если канал не указан то заглушает всех в голосовом канале автора команды.")
    @has_permissions(moderate_members=True)
    async def vcm(self, ctx: commands.Context, channel: discord.VoiceChannel = None) -> None:
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                embed = ViolaEmbed(ctx=ctx, format='error')
                embed.description = '**Укажите канал для выполнения этого действия.**'
                return await ctx.channel.send(embed=embed)
        ids = [self.bot.owner_id]
        done = False
        if not channel:
            await ctx.send("`s!vcm <channel_id | mention> заглушает всех в голосовом канале.`")
            return
        with suppress(Exception):
            if not channel: 
                return await ctx.send("`Канал не найден.`")
            if channel.guild.name != ctx.guild.name:
                return await ctx.send("`Канал не найден.`")
            for member in channel.members:
                if not member.id in ids:
                    await member.edit(mute=True, reason="voice_channel_mute")
                    done = True
            if done:
                await ctx.send(f'`Все участники в канале {channel.name} заглушены.`')
            else:
                await ctx.send(f'`В канале {channel.name} нет участников, которых можно заглушить.`')

    @commands.command(aliases = ['r', ], description ='Команда.\nПсевдонимы: `s!r <текст>`\nОтвечает от имени бота на сообщение другого пользователя.\n(Вам необходимо чтобы в сообщении с командой был ответ на то сообщение на которое вы хотите чтобы бот ответил.)')
    async def reply(self, ctx: commands.Context, *content) -> None:
        with suppress(Exception):
            async def d1(ctx: commands.Context):
                await ctx.message.delete()
            async def r2(ctx: commands.Context, content, message: discord.Message):
                await message.reply(content=' '.join(content))
            if not ctx.message.reference:
                return
            ref = ctx.message.reference
            message = self.bot.get_channel(ref.channel_id).get_partial_message(ref.message_id)
            self.bot.loop.create_task(d1(ctx))
            self.bot.loop.create_task(r2(ctx, content, message))

    @commands.command(description="Эту команду может использовать только мой создатель.")
    async def invite(self, ctx: commands.Context, id) -> None:
        if ctx.author.id == self.bot.owner_id:
            try:
                guild = self.bot.get_guild(int(id))
                channel = guild.categories[0].channels[0]
                invitelink = await channel.create_invite(max_uses=1)
                await ctx.author.send(invitelink)
            except Exception as e:
                await ctx.author.send(f'Something went wrong {e}\n{type(e)}')
    
    @commands.command()
    @has_permissions(administrator=True)
    async def specify(self, ctx: commands.Context, channel: discord.TextChannel=None) -> None:
        if channel is None:
            await self.bot.bd.remove({'guildid': ctx.guild.id}, category='system')
            return await ctx.channel.send(f'`функция отключена.`')
        res = await self.bot.bd.fetch({'guildid': ctx.guild.id}, category='system')
        if not res:
            await self.bot.bd.add({'guildid': ctx.guild.id, 'channelid': channel.id}, category='system')
        else:
            await self.bot.bd.remove({'guildid': ctx.guild.id}, category='system')
            await self.bot.bd.add({'guildid': ctx.guild.id, 'channelid': channel.id}, category='system')
        await ctx.channel.send(f'`Канал для сообщений бота теперь: `{channel.mention}')
    
    @commands.command()
    @has_permissions(administrator=True)
    async def settings(self, ctx: commands.Context):
        async with ctx.channel.typing():
            embed = ViolaEmbed(ctx=ctx)
            embed.description = ">>> Выберите ниже то что вам нужно."
            embed.title = 'Настройте ваш сервер так, как вы хотите.'
            await ctx.channel.send(embed=embed, view=OnSettings())
    
    @commands.command()
    @commands.is_owner()
    async def getav(self, ctx: commands.Context, member: discord.Member = None, format='welcome'):
        try:
            if member is None:
                member = ctx.author
            dfile = await self.bot.get_welcome_image(member=member, format=format)
            await ctx.channel.send(file=dfile)
        except Exception:
            print(traceback.format_exc())
    
    @commands.command()
    @has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member = None, reason: str = None) -> None:
        if member == None or member == ctx.message.author:
            embed = discord.Embed(title="Команда ban", description=f"`s!ban <@member> <Optional[reason]>`", colour=discord.Colour.brand_red())
            return await ctx.channel.send(embed=embed)
        if member.top_role >= ctx.author.top_role:
            await ctx.message.add_reaction('❌')
            return await ctx.channel.send('`Не удалось забанить участника так как его роли выше или равны вашим.`', delete_after=15.0)
        if not reason:
            try:
                await member.ban(reason=f'{ctx.author} {datetime.datetime.utcnow()} UTC')
                await ctx.message.add_reaction('✅')
            except discord.errors.Forbidden:
                await ctx.message.add_reaction('❌')
        else:
            try:
                await member.ban(reason=f'Причина: {reason}, {ctx.author} {datetime.datetime.utcnow()} UTC')
                await ctx.message.add_reaction('✅')
            except discord.errors.Forbidden:
                await ctx.message.add_reaction('❌')
        with suppress(Exception):
            await member.send(f'Вы были забанены на сервере {ctx.guild.name} по причине: {reason if reason else "Причина не указана."}')
    
    @commands.command()
    @has_permissions(moderate_members=True)
    async def mute(self, ctx: commands.Context, member: discord.Member = None, time: str = '27d23h59m59s', reason: str = None) -> None:
        try:
            pandas.to_timedelta(time)
        except Exception:
            return await ctx.channel.send('Неверный спецификатор времени. Убедитесь что в нем нет **русских** букв. Пример: `s!mute @user 15m bad_boi`')
        if member is None and ctx.message.reference is not None:
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = message.author
        if member.is_timed_out():
            return await ctx.channel.send('`Пользователь уже находится в таймауте.`')
        if member == None or member == ctx.message.author:
            embed = discord.Embed(title="Команда mute", description=f"`s!mute <@member> <Optional[reason]>`", colour=discord.Colour.brand_red())
            return await ctx.channel.send(embed=embed)
        if member.top_role >= ctx.author.top_role:
            await ctx.message.add_reaction('❌')
            return await ctx.channel.send('`Не удалось дать таймаут участнику так как его роли выше или равны вашим.`', delete_after=15.0)
        if not reason:
            try:
                timedelta = pandas.to_timedelta(time)
                if timedelta > datetime.timedelta(days=27, hours=23, minutes=59, seconds=59):
                    return await ctx.message.add_reaction('❌')
                await member.timeout(timedelta, reason=f'{ctx.author} {datetime.datetime.utcnow()} UTC')
                await ctx.message.add_reaction('✅')
            except Exception as e:
                print(e, 'timeout')
                await ctx.message.add_reaction('❌')
        else:
            try:
                timedelta = pandas.to_timedelta(time)
                if timedelta > datetime.timedelta(days=27, hours=23, minutes=59, seconds=59):
                    return await ctx.message.add_reaction('❌')
                await member.timeout(timedelta, reason=f'Причина: {reason}, {ctx.author} {datetime.datetime.utcnow()} UTC')
                await ctx.message.add_reaction('✅')
            except Exception:
                print(e, 'timeout reason')
                await ctx.message.add_reaction('❌')
# -----------------------------------------------------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(cmds(bot))

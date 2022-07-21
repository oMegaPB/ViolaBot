import traceback
import discord, asyncio, random
from discord.ext import commands
import emoji
# Reactions -----------------------------------------------------------------------------------------------------------
class ReactionsCallback(discord.ui.Select):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        options=[
            discord.SelectOption(label="Добавить параметр.",emoji="👌",description="Добавить параметр выдачи роли по реакции."),
            discord.SelectOption(label="Удалить параметр.",emoji="✨",description="Удалить параметр выдачи роли по реакции."),
            discord.SelectOption(label="Просмотр параметров.",emoji="🎭",description="Просмотреть все параметры на этом сервере.")
            ]
        super().__init__(placeholder="Выберите опцию.", max_values=1, min_values=1, options=options)
    def embed(self, description, interaction: discord.Interaction, format='Normal'):
        embed = discord.Embed(description=f'**{description}**')
        if format == 'Error':
            embed.title = 'Ошибка'
            embed.color = discord.Color.red()
        elif format == 'Normal':
            embed.title = 'Роли по реакции.'
            embed.color = 0x00ffff
        # embed.set_footer(text=f'{interaction.guild.name}', icon_url=f'{interaction.guild.icon}')
        return embed
    async def callback(self, interaction: discord.Interaction):
        def check(m: discord.Message):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        if self.values[0] == 'Добавить параметр.':
            args = []
            try:
                await interaction.response.send_message(embed=self.embed('Введите id канала:', interaction), ephemeral=True)
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                await msg.delete()
                channel = self.bot.get_channel(int(msg.content))
                if channel is None or channel.guild.id != interaction.guild_id or str(channel.type) != 'text':
                    await interaction.followup.send(embed=self.embed('Канал не найден среди текстовых каналов этого сервера.', interaction, format='Error'), ephemeral=True)
                    return
                args.append(channel.id)
                await interaction.followup.send(embed=self.embed('Введите id Сообщения:', interaction), ephemeral=True)
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                await msg.delete()
                message = await self.bot.get_channel(int(args[0])).fetch_message(int(msg.content))
                if message is None:
                    await interaction.followup.send(embed=self.embed('Сообщение не найдено.', interaction, format='Error'), ephemeral=True)
                    return
                args.append(message.id)
                await interaction.followup.send(embed=self.embed('Отправьте нужную вам реакцию в чат:', interaction), ephemeral=True)
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                if emoji.emoji_count(msg.content) == 1:
                    reaction = msg.content
                    await message.add_reaction(str(msg.content))
                    raw_reaction = msg.content
                elif emoji.emoji_count(msg.content) > 1:
                    await interaction.followup.send(embed=self.embed('Неверный формат.', interaction, format='Error'), ephemeral=True)
                    await msg.delete()
                    return
                else:
                    if msg.content.count(':') == 2 and msg.content.count('<') == 1 and msg.content.count('>') == 1:
                        reaction = msg.content[:len(msg.content)-20]
                        if msg.content.count('<a:') == 1:
                            reaction = reaction[3:]
                        else:
                            reaction = reaction[2:]
                        raw_reaction = msg.content
                        for x in self.bot.emojis:
                            if str(raw_reaction) == str(x):
                                await message.add_reaction(x)
                    else:
                        await interaction.followup.send(embed=self.embed('Неверный формат.', interaction, format='Error'), ephemeral=True)
                        await msg.delete()
                        return
                await msg.delete()
                args.append(reaction)
                await interaction.followup.send(embed=self.embed('Упомяните роль или отправьте ее id:', interaction), ephemeral=True)
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                await msg.delete()
                role = discord.utils.get(interaction.guild.roles, id=int(msg.content.replace('<@&', '').replace('>', '')))
                if role is not None:
                    args.append(role.id)
                else:
                    await interaction.followup.send(embed=self.embed('Роль не найдена', interaction, format='Error'), ephemeral=True)
                    return
                res = self.bot.bd.fetch({'guildid': interaction.guild.id, 'channel_id': args[0], 'message_id': args[1], 'reaction': args[2], 'role_id': args[3]}, category='reactroles')
                if res['success'] == 'False':
                    id = random.randint(100000, 999999)
                    res = self.bot.bd.add(
                        {'guildid': interaction.guild.id, 'channel_id': args[0], 'message_id': args[1], 'reaction': args[2], 'role_id': args[3], 'uniqid': id},
                        category='reactroles'
                    )
                else:
                    await interaction.followup.send(embed=self.embed('Такой параметр уже существует.', interaction, format='Error'), ephemeral=True)
                    return
                await interaction.followup.send(embed=discord.Embed(title='Роли за реакцию.', description=f'Параметр добавлен.\nКанал: <#{channel.id}>\nid сообщения: [**{message.id}**]({message.jump_url})\nРеакция: {raw_reaction}\nРоль: <@&{role.id}>\nID: {id}', color=discord.Color.green()), ephemeral=True)
            except asyncio.TimeoutError:
                return
        elif self.values[0] == 'Просмотр параметров.':
            await interaction.response.defer(thinking=True, ephemeral=True)
            res = self.bot.bd.fetch({'guildid': interaction.guild.id}, mode='all', category='reactroles')
            content = ''
            count = 0
            if res['success'] == 'True':
                for y in res['value']:
                    count += 1
                    channel = self.bot.get_channel(int(y['channel_id']))
                    message = await channel.fetch_message(int(y['message_id']))
                    content += f'**{count}.**\nКанал: <#{channel.id}>\nСообщение: [**[{message.id}]**]({message.jump_url})\nРеакция: {y["reaction"]}\nРоль: <@&{y["role_id"]}>\nID: {y["uniqid"]}\n'
                if content == '':
                    content = 'Параметров для этого сервера не найдено.'
                embed = discord.Embed(title='Все параметры связанные с этми сервером:', description=content)
                embed.color = 0x00ffff
                await interaction.followup.send(embed=embed)
                return
            else:
                await interaction.followup.send(embed=discord.Embed(title='Все параметры связанные с этми сервером:',description='Параметров для этого сервера не найдено.', color = 0x00ffff))
                return
        elif self.values[0] == 'Удалить параметр.':
            await interaction.response.send_message(embed=self.embed(f'Отправьте в чат id параметра:', interaction), ephemeral=True)
            try:
                try:
                    msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    return
                res = self.bot.bd.fetch({'uniqid': int(msg.content)}, category='reactroles')
                if res['success'] == 'True':
                    self.bot.bd.remove(res['value'], category='reactroles')
                    await interaction.followup.send(embed=self.embed(f'Параметр успешно удален.', interaction), ephemeral=True)
                    return
                else:
                    await interaction.followup.send(embed=self.embed(f'Параметр не найден.', interaction, format='Error'), ephemeral=True)
                    return
            except Exception as e:
                print(traceback.format_exc())
                await interaction.response.send_message(embed=self.embed(f'{e}', interaction, format='Error'), ephemeral=True)
class Reactions(discord.ui.View):
    def __init__(self, *, timeout = None, bot: commands.Bot = None):
        super().__init__(timeout=timeout)
        self.add_item(ReactionsCallback(bot))
# ----------------------------------------------------------------------------------------------------------------------
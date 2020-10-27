import os
from datetime import datetime
import random
import discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BOTCHANNEL_ID = os.getenv('BOTCHANNEL_ID')
ADMINGROUP_ID = os.getenv('ADMINGROUP_ID')

bot = commands.Bot(command_prefix='$')

@bot.event
async def on_ready():
    with open("botLog.log", "a+") as f:
        f.write(str(datetime.now()) + f" {bot.user.name} - {bot.user.id} login\n")

@bot.command(name='newProject', help='Erzeugt eine neue Kategorie')
async def newProject(ctx, projectName=""):
    channel = bot.get_channel(ctx.channel.id)
    if ctx.channel.id != int(BOTCHANNEL_ID):
        # if command in wrong channel
        await channel.send("Neue Projekte können nur im Botchannel angelegt werden 🤖")
        return
    else:
        if projectName == "":
            # if projectName not specified
            await channel.send("Gib ein Projektnamen an! 🤖")
            return
        else:
            existing_category = discord.utils.get(ctx.guild.categories, name=projectName)
            if existing_category:
                await channel.send(f"Ein Projekt mit dem Namen **{projectName}** existiert bereits 🤖!")
                return
            else:
                await channel.send(f'Neues Projekt {projectName} wird erstellt 🦾')
                # setting permissions
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
                    ctx.author: discord.PermissionOverwrite(read_messages=True)
                }
                category = await ctx.guild.create_category(projectName, overwrites = overwrites)
                await ctx.guild.create_text_channel("botbefehle", category=category)
                await ctx.guild.create_text_channel("chat 1", category=category)
    with open("botLog.log", "a+") as f:
        f.write(str(datetime.now()) + f" {ctx.author} - {ctx.command} cmd\n")


@bot.command(name='adminProject', help='Erzeugt eine neue Kategorie mit bestimmter anzahl channels (admins only)')
async def adminProject(ctx, projectName="", textChannels=1, voiceChannels=1):
    channel = bot.get_channel(ctx.channel.id)
    role = ctx.guild.get_role(int(ADMINGROUP_ID))
    if role not in ctx.author.roles:
        # user is not an admin
        await channel.send("💩👁 Du bist kein Administrator {}".format(ctx.author.mention))
        with open("botLog.log", "a+") as f:
            f.write(str(datetime.now()) + f" {ctx.author} - noAdminPerm cmd\n")
        return
        
    if ctx.channel.id != int(BOTCHANNEL_ID):
        # if command in wrong channel
        await channel.send("Neue Projekte können nur im Botchannel angelegt werden 🤖")
        return
    else:
        if projectName == "":
            # if projectName not specified
            await channel.send("Gib ein Projektnamen an! 🤖")
            return
        else:
            existing_category = discord.utils.get(
                ctx.guild.categories, name=projectName)
            if existing_category:
                await channel.send(f"Ein Projekt mit dem Namen **{projectName}** existiert bereits! 🤖")
                return
            else:
                await channel.send(f'Neues Projekt {projectName} wird erstellt 🦾')
                # setting permissions
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
                    ctx.author: discord.PermissionOverwrite(read_messages=True)
                }
                category = await ctx.guild.create_category(projectName, overwrites=overwrites)
                await ctx.guild.create_text_channel("botbefehle", category=category)
                for i in range(textChannels):
                    count = i + 1
                    await ctx.guild.create_text_channel(f"chat {count}", category=category)
                for j in range(voiceChannels):
                    count = j + 1
                    await ctx.guild.create_voice_channel(f"voice {count}", category=category)
    with open("botLog.log", "a+") as f:
        f.write(str(datetime.now()) + f" {ctx.author} - {ctx.command} cmd\n")

bot.run(TOKEN)



# print(ctx.channel)
# print(ctx.command)
# print(ctx.me)
# print(ctx.author)
# print(channel.created_at)
# bot = commands.Bot(command_prefix='!')

# @bot.command(name='99')
# async def nine_nine(ctx):
#     brooklyn_99_quotes = [
#         'I\'m the human form of the 💯 emoji.',
#         'Bingpot!',
#         (
#             'Cool. Cool cool cool cool cool cool cool, '
#             'no doubt no doubt no doubt no doubt.'
#         ),
#     ]

#     response = random.choice(brooklyn_99_quotes)
#     await ctx.send(response)

# bot.run(TOKEN)

# class MyClient(discord.Client):
#     # on login
#     async def on_ready(self):
#         print("släuft. bzzzz")
#     # on any message
#     async def on_message(self, message):
#         # check if bot is sender of message
#         if message.author == client.user:
#             return
#         if message.content.startswith("sup bot?"):
#             await message.channel.send("hi there " + str(message.author) + ", busy today... how are you doin?")
#             # print("Message from " + str(message.author) + ": " + str(message.content))

# client = MyClient()
# client.run(TOKEN)

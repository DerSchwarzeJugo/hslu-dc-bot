import os
import random
import discord
import asyncio
import re
import json
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BOTCHANNEL_ID = os.getenv('BOTCHANNEL_ID')
ADMINGROUP_ID = os.getenv('ADMINGROUP_ID')

bot = commands.Bot(command_prefix='$')

# if command not in botchannel
async def channelCheck(ctx, channel):
    if ctx.channel.id != int(BOTCHANNEL_ID):
        await channel.send("Dieses Kommando ist nur im botchannel gültig 🤖")
        return False
    return True

# if projectName not specified
async def projectNameCheck(projectName, channel):
    if projectName == "":
        await channel.send("Gib ein Projektnamen an! 🤖")
        return False
    return True

# if project already exists
async def categoryCheck(ctx, projectName):
    existing_category = discord.utils.get(ctx.guild.categories, name=projectName)
    channel = bot.get_channel(ctx.channel.id)
    if existing_category:
        await channel.send(f"Ein Projekt mit dem Namen **{projectName}** existiert bereits 🤖!")
        return False
    return True

# check if user in admingroup
async def adminCheck(ctx, channel):
    role = ctx.guild.get_role(int(ADMINGROUP_ID))
    if role not in ctx.author.roles:
        # user is not an admin
        await channel.send(f"💩👁 Du bist kein Administrator {ctx.author.mention}")
        with open("botLog.log", "a+") as f:
            f.write(str(datetime.now()) + f" {ctx.author} - noAdminPerm cmd\n")
        return False
    return True

# if command in a botbefehle channel
async def innerChannelCheck(ctx, channel):
    if  channel.name != "botbefehle":
        await channel.send("Neue Chats innerhalb von Projekten können nur im jeweiligen botbefehle channel angelegt werden 🤖")
        return False
    return True

# dockerstyle names for random chats
def getFancyName():
    name: str
    with open("names_left.json") as jsonFile:
        data = json.load(jsonFile)
        name = random.choice(data)
    with open("names_right.json") as jsonFile:
        data = json.load(jsonFile)
        name += "-" + random.choice(data)
    return name

@bot.event
async def on_ready():
    with open("botLog.log", "a+") as f:
        f.write(str(datetime.now()) + f" {bot.user.name} - {bot.user.id} login\n")


@bot.command(name='newProject', help='Erzeugt ein neues Projekt mit Textchat', aliases=["nP", "np"])
async def newProject(ctx, projectName=""):
    channel = bot.get_channel(ctx.channel.id)
    if not await channelCheck(ctx, channel) or not await projectNameCheck(projectName, channel) or not await categoryCheck(ctx, projectName):
        return
        
    await channel.send(f'Neues Projekt **{projectName}** wird erstellt 🦾')
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


@bot.command(name='adminProject', help='Erzeugt eine neue Kategorie mit bestimmter anzahl channels (admins only)', aliases=["aP", "ap"])
async def adminProject(ctx, projectName="", textChannels=1, voiceChannels=1):
    channel = bot.get_channel(ctx.channel.id)
    if not await adminCheck(ctx, channel) or not await channelCheck(ctx, channel) or not await projectNameCheck(projectName, channel) or not await categoryCheck(ctx, projectName):
        return
  
    await channel.send(f'Neues Projekt **{projectName}** wird erstellt 🦾')
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


@bot.command(name="deleteProject", help="Delete a project and all channels in it (admin only, careful!)", aliases=["dP", "dp"])
async def deleteProject(ctx, projectName=""):
    channel = bot.get_channel(ctx.channel.id)
    
    if not await adminCheck(ctx, channel) or not await channelCheck(ctx, channel) or not await projectNameCheck(projectName, channel):
        return

    category = discord.utils.get(ctx.guild.categories, name=projectName)
    if not category:
        await channel.send(f"Dieses Projekt existiert nicht 🤖!")
        return

    # confirmation function
    def check(m):
        return m.channel == channel and m.content == "ja"

    await channel.send(f"**{projectName}** wirklich löschen? Bestätige mit ja 🤖")
    # get confirmation if user really wants to delete a project
    try:
        await bot.wait_for('message', check=check, timeout=5.0)
    except asyncio.TimeoutError:
        await channel.send("du hast zu lange gebraucht 😷")
        return
    else:
        for tchannel in category.text_channels:
            await tchannel.delete()
        for vchannel in category.voice_channels:
            await vchannel.delete()
        await category.delete()
        await channel.send(f"Das projekt **{projectName}** wurde gelöscht von {ctx.author.mention} 🤖❌")
        with open("botLog.log", "a+") as f:
            f.write(str(datetime.now()) + f" {ctx.author} - {ctx.command} - {projectName} cmd\n")


@bot.command(name='newText', help='Erzeugt einen neuen Textchat', aliases=["nT", "nt"])
async def newText(ctx, tcName=""):
    channel = bot.get_channel(ctx.channel.id)
    if not await innerChannelCheck(ctx, channel):
        return
    
    if tcName == "":
        tcName = getFancyName()
    await channel.send(f'Neuer Textchannel **{tcName}** wird erstellt 🦾')
    await ctx.guild.create_text_channel(f"{tcName}", category=channel.category)


@bot.command(name='newVoice', help='Erzeugt einen neuen Voicechat', aliases=["nV", "nv"])
async def newVoice(ctx, vcName=""):
    channel = bot.get_channel(ctx.channel.id)
    if not await innerChannelCheck(ctx, channel):
        return

    if vcName == "":
        vcName = getFancyName()
    await channel.send(f'Neuer Voicechannel **{vcName}** wird erstellt 🦾')
    await ctx.guild.create_voice_channel(f"{vcName}", category=channel.category)
        

@bot.command(name="newUser", help="Fügt einen oder mehrere User einem Projekt hinzu", aliases=["nU", "nu"])
async def newUser(ctx, projectName=""):
    channel = bot.get_channel(ctx.channel.id)
    if not await channelCheck(ctx, channel) or not await projectNameCheck(projectName, channel):
        return

    category = discord.utils.get(ctx.guild.categories, name=projectName)
    if not category:
        await channel.send(f"Dieses Projekt existiert nicht 🤖!")
        return

    for mention in ctx.message.mentions:
        user = bot.get_user(mention.id)
        if not isinstance(user, discord.abc.User):
            await channel.send("Kein valider user. markiere mit @ und wähle die Person(en) aus der Liste 🤖")
            return
        await category.set_permissions(user, read_messages=True)
        await channel.send(f"User {user} wurde dem Projekt {projectName} hinzugefügt 🤖")
        return
    # only happening if ctx.message.mentions is empty
    await channel.send("Keine validen User angegeben 🤖")
    


# run this shit
bot.run(TOKEN)

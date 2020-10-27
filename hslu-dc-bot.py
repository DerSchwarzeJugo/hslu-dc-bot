import os
import random
import discord
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BOTCHANNEL_ID = os.getenv('BOTCHANNEL_ID')
ADMINGROUP_ID = os.getenv('ADMINGROUP_ID')

bot = commands.Bot(command_prefix='$')

async def channelCheck(ctx, channel):
    # if command in wrong channel
    if ctx.channel.id != int(BOTCHANNEL_ID):
        await channel.send("Neue Projekte können nur im Botchannel angelegt werden 🤖")
        return False
    return True

async def projectNameCheck(projectName, channel):
    # if projectName not specified
    if projectName == "":
        await channel.send("Gib ein Projektnamen an! 🤖")
        return False
    return True

async def categoryCheck(ctx, projectName):
    # if project already exists
    existing_category = discord.utils.get(ctx.guild.categories, name=projectName)
    channel = bot.get_channel(ctx.channel.id)
    if existing_category:
        await channel.send(f"Ein Projekt mit dem Namen **{projectName}** existiert bereits 🤖!")
        return False
    return True

async def adminCheck(ctx, channel):
    role = ctx.guild.get_role(int(ADMINGROUP_ID))
    if role not in ctx.author.roles:
        # user is not an admin
        await channel.send(f"💩👁 Du bist kein Administrator {ctx.author.mention}")
        with open("botLog.log", "a+") as f:
            f.write(str(datetime.now()) + f" {ctx.author} - noAdminPerm cmd\n")
        return False
    return True


@bot.event
async def on_ready():
    with open("botLog.log", "a+") as f:
        f.write(str(datetime.now()) + f" {bot.user.name} - {bot.user.id} login\n")


@bot.command(name='newProject', help='Erzeugt ein neues Projekt mit Textchat', aliases=["nP", "np", "newP"])
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


@bot.command(name='adminProject', help='Erzeugt eine neue Kategorie mit bestimmter anzahl channels (admins only)', aliases=["aP", "ap", "adP", "adminP"])
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


@bot.command(name="deleteProject", help="Delete a project and all channels in it (admin only, careful!)", aliases=["dP", "dp", "delP", "deleteP"])
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


# run this shit
bot.run(TOKEN)

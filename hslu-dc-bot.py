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

# set up the bot object
bot = commands.Bot(command_prefix='$', help_command=None)

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

# botchannel help
async def setUpHelpEmbed(ctx):
    cp = bot.command_prefix
    embed = discord.Embed(
        colour=discord.Colour.gold(),
        title="BotHelp",
        description=f"{cp}help Zeigt dieses Menü"
    )
    adEmbed = discord.Embed(
        colour=discord.Colour.red(),
        title="BotHelp",
        description=f"Admins functions"
    )
    # botchannel help
    if ctx.channel.id == int(BOTCHANNEL_ID):
        help = f'[{cp}np | {cp}nP] \nErzeugt ein neues Projekt mit einem Textchat\n--> {cp}newProject NAME || {cp}np "name mit abständen"'
        embed.add_field(name=f"{cp}newProject", value=help, inline=False)
        help = f"[{cp}nu | {cp}nU] \nFügt einen oder mehrere User einem Projekt hinzu\n--> {cp}newUser PROJECT @USER [@USER...]"
        embed.add_field(name=f"{cp}newUser", value=help, inline=False)
        await ctx.channel.send(embed=embed)
    
        role = ctx.guild.get_role(int(ADMINGROUP_ID))
        if role in ctx.author.roles:
            help = f'[{cp}ap | {cp}aP] \nNeue Kategorie mit multiplen Text & Voice channels\n--> {cp}ap NAME T V'
            adEmbed.add_field(name=f"{cp}adminProject", value=help, inline=False)
            help = f"[{cp}dp | {cp}dP] \nProjekt inkl. aller channels löschen\n--> {cp}dP NAME"
            adEmbed.add_field(name=f"{cp}deleteProject", value=help, inline=False)
            await ctx.channel.send(embed=adEmbed)

# botbefehle help
async def setUpInlineHelpEmbed(channel):
    cp = bot.command_prefix
    embed = discord.Embed(
        colour=discord.Colour.gold(),
        title="BotHelp",
        description=f"{cp}help Zeigt dieses Menü"
    )
    if channel.name == "botbefehle":
        help = f'[{cp}nt | {cp}nT] \nErzeugt einen neuen Textchat in diesem Projekt\n--> {cp}newText | {cp}newText NAME'
        embed.add_field(name=f"{cp}newText", value=help, inline=False)
        help = f'[{cp}nV | {cp}nV] \nErzeugt einen neuen Voicechat in diesem Projekt\n--> {cp}nv | {cp}nv NAME'
        embed.add_field(name=f"{cp}newVoice", value=help, inline=False)
        await channel.send(embed=embed)

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


@bot.command(name="help", aliases=["HELP","helpp","heelp"])
async def help(ctx):
    await setUpHelpEmbed(ctx)
    await setUpInlineHelpEmbed(ctx.channel)


@bot.command(name='newProject', aliases=["nP", "np"])
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
    botchannel= await ctx.guild.create_text_channel("botbefehle", category=category)
    await ctx.guild.create_text_channel("chat 1", category=category)
    await setUpInlineHelpEmbed(botchannel)
    with open("botLog.log", "a+") as f:
        f.write(str(datetime.now()) + f" {ctx.author} - {ctx.command} cmd\n")


@bot.command(name='adminProject', aliases=["aP", "ap"])
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
    botchannel = await ctx.guild.create_text_channel("botbefehle", category=category)
    await setUpInlineHelpEmbed(botchannel)
    for i in range(textChannels):
        count = i + 1
        await ctx.guild.create_text_channel(f"chat {count}", category=category)
    for j in range(voiceChannels):
        count = j + 1
        await ctx.guild.create_voice_channel(f"voice {count}", category=category)
    with open("botLog.log", "a+") as f:
        f.write(str(datetime.now()) + f" {ctx.author} - {ctx.command} cmd\n")


@bot.command(name="deleteProject", aliases=["dP", "dp"])
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


@bot.command(name='newText', aliases=["nT", "nt"])
async def newText(ctx, tcName=""):
    channel = bot.get_channel(ctx.channel.id)
    if not await innerChannelCheck(ctx, channel):
        return
    
    if tcName == "":
        tcName = getFancyName()
    await channel.send(f'Neuer Textchannel **{tcName}** wird erstellt 🦾')
    await ctx.guild.create_text_channel(f"{tcName}", category=channel.category)
    with open("botLog.log", "a+") as f:
        f.write(str(datetime.now()) + f" {ctx.author} - {ctx.command} cmd\n")


@bot.command(name='newVoice', aliases=["nV", "nv"])
async def newVoice(ctx, vcName=""):
    channel = bot.get_channel(ctx.channel.id)
    if not await innerChannelCheck(ctx, channel):
        return

    if vcName == "":
        vcName = getFancyName()
    await channel.send(f'Neuer Voicechannel **{vcName}** wird erstellt 🦾')
    await ctx.guild.create_voice_channel(f"{vcName}", category=channel.category)
    with open("botLog.log", "a+") as f:
        f.write(str(datetime.now()) + f" {ctx.author} - {ctx.command} cmd\n")
        

@bot.command(name="newUser", aliases=["nU", "nu"])
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
            await channel.send("Kein valider user. Markiere mit @ und wähle die Person(en) aus der Liste 🤖")
            return
        await category.set_permissions(user, read_messages=True)
        await channel.send(f"User {user} wurde dem **Projekt** {projectName} hinzugefügt 🤖")
        with open("botLog.log", "a+") as f:
            f.write(str(datetime.now()) + f" {ctx.author} - {ctx.command} - {user} - {projectName} cmd\n")
        return
    # only happening if ctx.message.mentions is empty
    await channel.send("Keine validen User angegeben 🤖")
    


# run this shit
bot.run(TOKEN)

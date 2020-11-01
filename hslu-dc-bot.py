import os
import random
import discord
import asyncio
import re
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from discord.ext import commands, tasks

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BOTCHANNEL_ID = os.getenv('BOTCHANNEL_ID')
ADMINGROUP_ID = os.getenv('ADMINGROUP_ID')
SERVER_ID = os.getenv('SERVER_ID')

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

# if command in a botcommands channel
async def innerChannelCheck(ctx, channel):
    if  channel.name != "botcommands":
        await channel.send("Neue Chats innerhalb von Projekten können nur im jeweiligen botcommands channel angelegt werden 🤖")
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
            help = f"[{cp}arch] \nProjekt inkl. aller channels archivieren\n--> {cp}arch NAME"
            adEmbed.add_field(name=f"{cp}archive", value=help, inline=False)
            await ctx.channel.send(embed=adEmbed)

# botcommands help
async def setUpInlineHelpEmbed(channel):
    cp = bot.command_prefix
    embed = discord.Embed(
        colour=discord.Colour.gold(),
        title="BotHelp",
        description=f"{cp}help Zeigt dieses Menü"
    )
    if channel.name == "botcommands":
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


    for guild in bot.guilds:
        if guild.id == int(SERVER_ID):
            # this creates our automated archive tasks
            while True:
                await autoArchive(guild)
                await checkChannelUsage(guild)
                # execute every x seconds
                await asyncio.sleep(10)
        else:
            continue


@bot.command(name="help", aliases=["HELP","helpp","heelp","h"])
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
    await category.edit(position=0)
    botchannel= await ctx.guild.create_text_channel("botcommands", category=category)
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
    await category.edit(position=0)
    botchannel = await ctx.guild.create_text_channel("botcommands", category=category)
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
        return m.channel == channel and m.content == "ja" or m.content == "Ja"

    await channel.send(f"**{projectName}** wirklich löschen? Bestätige mit ja 🤖")
    # get confirmation if user really wants to delete a project
    try:
        await bot.wait_for('message', check=check, timeout=5.0)
    except asyncio.TimeoutError:
        await channel.send("du hast zu lange gebraucht 😷")
        return
    else:
        for tchannel in category.text_channels:
            await tchannel.delete(reason="Manuell gelöscht")
        jsonFile = open("voiceChatLog.json", "r")
        data = json.load(jsonFile)
        for vchannel in category.voice_channels:
            if data:
                # remove current channel from the log
                newJsonData = [d for d in data if d.get("id") != vchannel.id]
                with open("voiceChatLog.json", "w") as file:
                    json.dump(newJsonData, file, indent=4)
            await vchannel.delete(reason="Manuell gelöscht")
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

    counter = 0
    for mention in ctx.message.mentions:
        user = bot.get_user(mention.id)
        if not isinstance(user, discord.abc.User):
            await channel.send("Kein valider user. Markiere mit @ und wähle die Person(en) aus der Liste 🤖")
            continue
        await category.set_permissions(user, read_messages=True)
        await channel.send(f"User **{user}** wurde dem Projekt **{projectName}** hinzugefügt 🤖")
        with open("botLog.log", "a+") as f:
            f.write(str(datetime.now()) + f" {ctx.author} - {ctx.command} - {user} - {projectName} cmd\n")
        counter+=1
    
    if counter == 0:
        # only happening if ctx.message.mentions is empty
        await channel.send("Keine validen User angegeben 🤖")
    

@bot.command(name="archive", aliases=["arch"])
async def archive(ctx, projectName=""):
    channel = bot.get_channel(ctx.channel.id)

    if not await adminCheck(ctx, channel) or not await channelCheck(ctx, channel) or not await projectNameCheck(projectName, channel):
        return

    category = discord.utils.get(ctx.guild.categories, name=projectName)
    if not category:
        await channel.send(f"Dieses Projekt existiert nicht 🤖!")
        return

    # confirmation function
    def check(m):
        return m.channel == channel and m.content == "ja" or m.content == "Ja"

    await channel.send(f"**{projectName}** wirklich archivieren? Bestätige mit ja 🤖")
    # get confirmation if user really wants to archive a project
    try:
        await bot.wait_for('message', check=check, timeout=5.0)
    except asyncio.TimeoutError:
        await channel.send("du hast zu lange gebraucht 😷")
        return
    else:
        # move to end of all projects
        newPosition = len(ctx.guild.categories)
        # overwriting the permissions
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
        }
        for tchannel in category.text_channels:
            await tchannel.edit(overwrites=overwrites)
        
        jsonFile = open("voiceChatLog.json", "r")
        data = json.load(jsonFile)
        for vchannel in category.voice_channels:
            if data:
                # remove current channel from the log
                newJsonData = [d for d in data if d.get("id") != vchannel.id]
                with open("voiceChatLog.json", "w") as file:
                    json.dump(newJsonData, file, indent=4)
            await vchannel.delete(reason="Automatisch gelöscht, da das Projekt archiviert wurde")

        await category.edit(name=f"archive-{projectName}", reason="Manuell ins Archiv verschoben", position=newPosition, overwrites= overwrites)
        await channel.send(f"Das Projekt **{projectName}** wurde archiviert von {ctx.author.mention} 🤖🗄️")
        with open("botLog.log", "a+") as f:
            f.write(str(datetime.now()) +
                    f" {ctx.author} - {ctx.command} - {projectName} cmd\n")

# define a looping function
async def autoArchive(guild):
    for category in guild.categories:
        # dont rearchive already archived stuff
        if str(category).startswith("archive"):
            continue
        projectName = str(category)
        # discord gives us utc time, so we have to plus one to get utc 2
        timeSinceCreation = datetime.now() - (category.created_at + timedelta(hours=1))
        # archive a projet automatically after 6 months
        if timeSinceCreation.seconds >= 60*60*24*30*6:
            # move to end of all projects
            newPosition = len(guild.categories)
            # overwriting the permissions
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
            }
            for tchannel in category.text_channels:
                await tchannel.edit(overwrites=overwrites)

            jsonFile = open("voiceChatLog.json", "r")
            data = json.load(jsonFile)
            for vchannel in category.voice_channels:
                if data:
                    # remove current channel from the log
                    newJsonData = [d for d in data if d.get("id") != vchannel.id]
                    with open("voiceChatLog.json", "w") as file:
                        json.dump(newJsonData, file, indent=4)
                await vchannel.delete(reason="Automatically deleted because project got archived")

            await category.edit(name=f"archive-{projectName}", reason="Moved to archive automatically", position=newPosition, overwrites=overwrites)
            botchannel = discord.utils.get(guild.channels, id=int(BOTCHANNEL_ID))
            await botchannel.send(f"Das Projekt **{projectName}** wurde automatisch archiviert von {guild.me} 🤖🗄️")
            with open("botLog.log", "a+") as f:
                f.write(str(datetime.now()) + f" {guild.me} - AutoArchive - {projectName} cmd\n")

# checks channel usage and auto deletes unused things
async def checkChannelUsage(guild):
    for category in guild.categories:
        # ignore archived stuff
        if str(category).startswith("archive"):
            continue
        botcommandsChannel = discord.utils.get(category.text_channels, name="botcommands")
        botchannel = discord.utils.get(guild.text_channels, name="botchannel")
        # if only one textchannel in project
        if len(category.text_channels) == 1 and category.text_channels[0] == botcommandsChannel and len(category.voice_channels) == 0:
            soonDeletedMessage = f"Dieses Projekt wird aufgrund von Inaktivität in **30 min** gelöscht. \nErstelle einen neuen Text- oder Voicechat und nutze ihn, unbenutzte Voicechats werden 30 min nach Erstellung gelöscht, unbenutzte Textchats werden 7 Tage nach Erstellung gelöscht. Projekte ohne Channel werden nach 30 min gelöscht 🤖"
            lastMessage = await botcommandsChannel.fetch_message(botcommandsChannel.last_message_id)
            if lastMessage.content == soonDeletedMessage and lastMessage.author == guild.me:
                timeSinceMessage = datetime.now() - (lastMessage.created_at + timedelta(hours=1))
                goneTime = 60*30
                if timeSinceMessage.seconds >= goneTime:
                    await botchannel.send(f"Das Projekt **{category.name}** wurde aufgrund von Inaktivität gelöscht")
                    await botcommandsChannel.delete(reason="Automatisch gelöscht aufgrund von Inaktivität")
                    await category.delete(reason="Automatisch gelöscht aufgrund von Inaktivität")
                    with open("botLog.log", "a+") as f:
                        f.write(str(datetime.now()) + f" {guild.me} - autoDelete Project - {category.name} cmd\n")
                
            else:
                await botcommandsChannel.send(soonDeletedMessage)

        for tchannel in category.text_channels:
            if str(tchannel) != "botcommands":
                # get time since creation, discord time is utc
                timeSinceCreation = datetime.now() - (tchannel.created_at + timedelta(hours=1))
                soonDeletedMessage = f"Dieser Textchannel wird aufgrund von Inaktivität in **5 min** gelöscht. Poste eine Nachricht darin um dies zu verhindern 🤖"
                
                # warn channel will be deleted if still unused after a week
                goneTime = 60*60*24*7
                if not tchannel.last_message_id and timeSinceCreation.seconds >= goneTime:
                    await tchannel.send(soonDeletedMessage)
                
                goneTime += 300
                # delete if still unused after 5 more minutes
                if timeSinceCreation.seconds >= goneTime:
                    lastMessage = await tchannel.fetch_message(tchannel.last_message_id)
                    if lastMessage.content == soonDeletedMessage and lastMessage.author == guild.me:
                        await tchannel.delete(reason="Automatisch gelöscht aufgrund von Inaktivität")
                        await botcommandsChannel.send(f"Der Textchannel **{tchannel.name}** wurde aufgrund von Inaktivität gelöscht 🤖")
                        with open("botLog.log", "a+") as f:
                            f.write(str(datetime.now()) + f" {guild.me} - autoDelete Textchannel - {tchannel.name} cmd\n")

        for vchannel in category.voice_channels:
            currentVoiceState = vchannel.voice_states
            if currentVoiceState:
                entryAdded = False
                # writing creation to log
                jsonFile = open("voiceChatLog.json", "r")
                data = json.load(jsonFile)
                if not data:
                    # create very first entry
                    voiceLog = {
                        "timestamp": str(datetime.now())
                    }
                    voiceEntry = {
                        "id": vchannel.id,
                        "name": vchannel.name,
                        "category_id": vchannel.category.id,
                        "created_at": str(vchannel.created_at),
                        "usage": [voiceLog]
                    }
                    data.append(voiceEntry)
                    entryAdded = True
                else:
                    for d in data:
                        # check if this channel already exists
                        if d.get("id") == vchannel.id:
                            voiceLog = {
                                "timestamp": str(datetime.now())
                            }
                            d.get("usage").append(voiceLog)
                            entryAdded = True

                    if not entryAdded:
                        # create new entry
                        voiceLog = {
                            "timestamp": str(datetime.now())
                        }
                        voiceEntry = {
                            "id": vchannel.id,
                            "name": vchannel.name,
                            "category_id": vchannel.category.id,
                            "created_at": str(vchannel.created_at),
                            "usage": [voiceLog]
                        }
                        data.append(voiceEntry)
                        entryAdded = True

                with open("voiceChatLog.json", "w") as file:
                    json.dump(data, file, indent=4)

            # delete unused channels
            jsonFile = open("voiceChatLog.json", "r")
            data = json.load(jsonFile)
            shouldDelete = True
            if data:
                for d in data:
                    if d.get("id") == vchannel.id:
                        shouldDelete = False

            timeSinceCreation = datetime.now() - (vchannel.created_at + timedelta(hours=1))
            # delete if not used at all after 30 minutes
            if shouldDelete and timeSinceCreation.seconds >= 60*30:
                await vchannel.delete(reason="Automatisch gelöscht aufgrund von Inaktivität")
                await botcommandsChannel.send(f"Der Voicechannel **{vchannel.name}** wurde aufgrund von Inaktivität gelöscht 🤖")
                with open("botLog.log", "a+") as f:
                    f.write(str(datetime.now()) + f" {guild.me} - autoDelete Voicechannel - {vchannel.name} cmd\n")



# run this shit
bot.run(TOKEN)

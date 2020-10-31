# hslu-dc-bot
A simple discord bot for our School-Channel on discord.

Creating new Projects (new category + channels for communication) and setting permissions, so not everybody gets spammed.
Possibility to add more channels inside the category, as well as adding permissions to the created category for other users.

For visibility purposes, projects can not be named the same like others (channels can).
Also Commands are only allowed in a specific channel

Legend:

CAPITAL = parameters
[] = optional arguments
$ = command prefix

$help can be typed in the botchannel and in the created Projects inside the botcommands channel to show this help section


Examples of possible commands in the botchannel:

Create Project

$newProject PROJECTNAME

$newProject "PROJECT NAME WITH SPECIAL CHARACTERS"

Adding Users to created projects (visibility purposes), u can specify multiple at once

$newUser PROJECTNAME @user1 [@user2 @user3 ...]

Admins can create projects with multiple channels at once (x = amount of textchannels, y = amount of voicechannels)

$adminProject PROJECTNAME [X Y]

Admins can also delete projects. After using the command u will be asked to confirm the deletion

$deleteProject PROJECTNAME

Examples of possible commands in the created projects botcommands channel:

Create a new textchat (name is optional, checkout for some docker names magic 🤘)

$newText [CHANNELNAME]

Create a new voicechat (name is optional aswell)

$newVoice [CHANNELNAME]

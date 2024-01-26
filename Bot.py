import discord
from discord.ext import commands
import random
import logging
import os
from dotenv import load_dotenv

load_dotenv(override=True)
from Tasks import Tasks
from ApproveTasks import ApproveTasks
from Data import *
import Queries
from Util import *
import asyncio

#
# CONSTANTS
#

# AUTH
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_SHEETS_KEY = os.getenv("GOOGLE_SHEETS_KEY")
DB_LOCALHOST = os.getenv("MYSQL_LOCALHOST")
DB_USER_NAME = os.getenv("MYSQL_USER_NAME")
DB_PW = os.getenv("MYSQL_PW")
WISE_OLD_MAN_COMPETITION_KEY = 36530
# TEST CHANNELS & WEBHOOKS
# Logic's Server
TEST_SUBMISSIONS_CHANNEL = 1194832130962890842
TEST_LOGS_CHANNEL = 1194488938480537740
TEST_WEBHOOK_USER_ID = 1194889597738549298
# LIVE CHANNELS & WEBHOOKS
BINGO_GENERAL_CHANNEL = 1193039460980502578
BINGO_LOGS_CHANNEL = 1195530905398284348
WEBHOOK_USER_ID = 1195911136021852191

BINGO_TEAM_CHANNELS = {
    "The Fat Woodcocks": 1197945391929368596,
    "Seczey's Revenge": 1197945547714207805,
    "TFK": 1197945883585675354,
    "The Real World Traders": 1197946038179352696,
    "BBBBB": 1197946114356289587,
    "Phased and Confused": 1197946234384691301,
}
# foki, me
ADMIN_RIGHTS = [453652490274078720, 545728431917236226]
# URLs & MESSAGES
EMBED_ICON_URL = "https://shorturl.at/wGOXY"
RULES_POST_URL = "https://discord.com/channels/741153043776667658/1193039460980502578/1193042254751879218"
RULES_POST_MSG = 1193042254751879218

#
# VARIABLES
#

# AUTH
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!bingo", intents=intents)
wom_client = wom.Client()
# TEST
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

#
# BOT COMMANDS
#

# TODO: memory leak??
# TODO: IMPORTANT--prevent double submissions
# TODO: "who called what" command logs?
# TODO: divide code into packaged files
# TODO: write bot start-up batch script
# TODO: match team color to profile embed, or random colors
# TODO: add toggleable options
# TODO: convert all images to discord.File local images


# "!bingotest" command
# For testing purposes
@bot.command()
async def test(ctx) -> None:
    #await ctx.send("http://tinyurl.com/s8aw585y")
    pass


# GLOBAL COMMANDS


# "!bingowhen" command
# Ping pong
@bot.command()
async def when(ctx) -> None:
    await ctx.channel.send("👀")
    return


# "!bingoinfo" command
# Displays information about the bingo event
@bot.command()
async def info(ctx) -> None:
    bingo_info_embed = discord.Embed(
        title=f"Battle Bingo Information", url=RULES_POST_URL, color=0x00FFDD
    )
    bingo_info_embed.set_author(
        name=bot.user.display_name, icon_url=bot.user.display_avatar
    )
    bingo_info_embed.set_thumbnail(url=EMBED_ICON_URL)
    bingo_info_embed.add_field(
        name="Start Date:",
        value="Thursday, January 25th, 9:30pm EST\nafter the clan meeting",
    )
    bingo_info_embed.add_field(name="Duration:", value="3 weeks")
    bingo_info_embed.add_field(name="Cost to Enter:", value="10M GP per person")
    bingo_info_embed.add_field(name="", value="", inline=False)
    bingo_info_embed.add_field(name="Current prize pool:", value="Over 2 BILLION GP")
    bingo_info_embed.add_field(name="Second place prize:", value="Refunded entry fee")
    bingo_info_embed.add_field(name="Points Achieveable:", value="200")
    bingo_info_embed.add_field(name="", value="", inline=False)
    bingo_info_embed.add_field(
        name="Win Condition:",
        value="First team to blackout the standard board OR the team with the most points by event end is the winner.",
        inline=False,
    )
    bingo_info_embed.add_field(
        name="",
        value="Each day for the first ten days a new batch of tiles will release between 5:30-6:00 PM EST",
        inline=False,
    )
    bingo_info_embed.add_field(name="", value="Watch for a Discord ping!", inline=False)
    bingo_info_embed.add_field(name="", value="", inline=False)
    bingo_info_embed.add_field(name="The Fat Woodcocks", value="Captain: Hokumpoke")
    bingo_info_embed.add_field(name="Seczey's Revenge", value="Captain: Seczey")
    bingo_info_embed.add_field(name="TFK", value="Captain: Kyanize")
    bingo_info_embed.add_field(
        name="The Real World Traders", value="Captain: ItsOnlyPrime"
    )
    bingo_info_embed.add_field(name="BBBBB", value="Captain: Blepe")
    bingo_info_embed.add_field(name="Phased and Confused", value="Captain: Unphased")

    await ctx.send(embed=bingo_info_embed)
    return


# "!bingome" command
# Displays custom bingo player profile card in an embed
@bot.command()
async def me(ctx) -> None:
    global player_titles_dict

    # Getting member and if they're a captain
    team, isCaptain = await find_bingo_team(ctx.author)
    if team == None:
        await ctx.channel.send(
            "You are not in the bingo.  RIP you.  Try and catch the next one!"
        )
        return
    elif team == "Bingo":
        team = "Bingo Participant"
    # Player custom title
    title = player_titles_dict.get(random.randint(1, len(player_titles_dict)))
    # Player custom smack_talk/quote
    smack_talk = get_smack_talk(team)
    gained = await wise_old_man(ctx, wom_client)
    # Custom settings for team captains
    if isCaptain:
        bingo_profile_embed = discord.Embed(
            description="👑 Team Captain",
            title=f"Battle Bingo Player Stats",
            color=0xFFAB00,
        )
    # Normal players
    else:
        bingo_profile_embed = discord.Embed(
            title=f"Battle Bingo Player Stats", color=0x0000FF
        )

    bingo_profile_embed.set_author(
        name=f"{ctx.author.display_name} the {title}",
        icon_url=ctx.author.avatar,
    )
    bingo_profile_embed.set_thumbnail(url=EMBED_ICON_URL)
    bingo_profile_embed.add_field(name="Team:", value=team, inline=True)
    bingo_profile_embed.add_field(name="XP Gained:", value=gained)
    bingo_profile_embed.add_field(name="", value=smack_talk, inline=False)

    await ctx.send(embed=bingo_profile_embed)
    return


# "!bingotasks" command
# Displays list of ALL tasks
# done
@bot.command()
async def tasks(ctx) -> None:
    view = Tasks(ctx.author)
    view.data = list(task_list.values())

    await view.send(ctx)
    return

# "!bingomenu" command
# Displays the bingo menu
@bot.command()
async def menu(ctx) -> None:
    bingo_info_embed = discord.Embed(
        title=f"Foki Bot Commands",
        color=0x00FFDD,
        description="Type these commands in any chat.",
    )
    bingo_info_embed.set_author(
        name=bot.user.display_name, icon_url=bot.user.display_avatar
    )
    bingo_info_embed.set_thumbnail(url=EMBED_ICON_URL)
    bingo_info_embed.add_field(
        name="General Use Commands", value="", inline=False
    )  # title
    bingo_info_embed.add_field(name="!bingomenu", value="This menu.", inline=True)
    bingo_info_embed.add_field(
        name="!bingoinfo", value="Information about the bingo event.", inline=True
    )
    bingo_info_embed.add_field(
        name="!bingome", value="Your bingo player card.", inline=True
    ),
    bingo_info_embed.add_field(name="", value=" ", inline=False)  # divider
    bingo_info_embed.add_field(
        name="!bingorules", value="The official bingo rules.", inline=True
    )
    bingo_info_embed.add_field(name="!bingowhen", value="Ping pong.", inline=True)
    bingo_info_embed.add_field(
        name="!bingotasks",
        value="Shows a list of all currently available bingo tasks.",
        inline=True,
    )
    bingo_info_embed.add_field(name="", value=" ", inline=False)  # divider
    bingo_info_embed.add_field(
        name="!bingosubmit X",
        value="Tile Submission Tool, used to submit your tile completion screenshots.  X = Task #",
        inline=True,
    )
    bingo_info_embed.add_field(
        name="!bingohowto",
        value="Instructions on how to post a bingo submission with the bot.",
        inline=True,
    )
    bingo_info_embed.add_field(
        name="!bingostatus",
        value="UNDER CONSTRUCTION.  Used to display your teams current bingo status.",
        inline=True,
    )
    bingo_info_embed.add_field(name="Admin Commands", value="", inline=False)  # title
    bingo_info_embed.add_field(
        name="!bingoapprove", value="ADMIN USE ONLY.  Approve submissions.", inline=True
    )
    bingo_info_embed.add_field(
        name="!bingorange X Y",
        value="ADMIN USE ONLY.  Set range of tasks currently available.  X = start of range, Y = end of range",
        inline=True,
    )
    bingo_info_embed.add_field(
        name="!bingoquit", value="ADMIN USE ONLY.  Turns the bot off.", inline=True
    )
    bingo_info_embed.add_field(name="", value="", inline=False)  # divider

    await ctx.send(embed=bingo_info_embed)
    return

# "!bingorules" command
# Display the bingo rules
@bot.command()
async def rules(ctx):
    bingo_rules_embed = discord.Embed(title=f"General Bingo Rules", color=0x00FFDD)
    bingo_rules_embed.set_author(
        name=bot.user.display_name, icon_url=bot.user.display_avatar
    )
    bingo_rules_embed.set_thumbnail(url=EMBED_ICON_URL)
    bingo_rules_embed.add_field(
        name="1.",
        value="All screenshots submitted must contain: the bingo keyword, the name of the user who obtained the drop, proof of the drop (chat message, loot on the ground, etc,) and any other tile-specific identifying information.  It is preferred that you just submit a screenshot of your entire RuneLite window or phone screen.  Submissions without these items will not be accepted, no exceptions.",
        inline=False,
    )
    bingo_rules_embed.add_field(
        name="2.",
        value="All submissions will be posted in the appropriate team private channel.",
        inline=False,
    )
    bingo_rules_embed.add_field(
        name="3.",
        value="Don't do a name change during bingo. It screws up your tracking and you won't get credit for completing tiles.",
        inline=False,
    )
    bingo_rules_embed.add_field(
        name="4.",
        value="A drop has to be in your name to count for tile completion. Content may be done in mixed groups, however any drops will only count toward the team of the person who obtained the drop.",
        inline=False,
    )
    bingo_rules_embed.add_field(
        name="5.",
        value='For any of the "most" style challenge tasks; you decide when to stop and what your best is. These will be blind submissions I reveal at the end.',
        inline=False,
    )
    bingo_rules_embed.add_field(name="", value="", inline=False)
    bingo_rules_embed.add_field(
        name="Alts:",
        value="From January 25th through February 11th at Midnight CST, see Discord post [here](https://discord.com/channels/741153043776667658/1193039460980502578/1194298395616083978) for what's allowed regarding alts.",
        inline=False,
    )
    bingo_rules_embed.add_field(
        name="",
        value="Starting at 12am CST on February 12th alts can go wild! This allows using alts in any way that is NOT working on different tiles at the same time.",
        inline=False,
    )
    bingo_rules_embed.add_field(
        name="",
        value="For the entire event (even the last three days), you will be banned from bingo if caught working on multiple tiles on different accounts at the same time or using an alt in a non-approved way.",
        inline=False,
    )
    bingo_rules_embed.add_field(
        name="",
        value="If you plan to play on multiple accounts, I WILL ONLY TRACK THE ACCOUNT IN WISEOLDMAN. Pick one and let me know before bingo starts. I don't care what account you complete tiles on, so long as you know I will only track one for xp/kc tiles.",
        inline=False,
    )
    bingo_rules_embed.add_field(
        name="Prep:",
        value="Prep anything you want EXCEPT things like storing raids purples.",
    )

    bingo_rules_embed2 = discord.Embed(
        title=f"Battle Bingo Competition Rules", color=0x00FFDD
    )
    bingo_rules_embed2.set_author(
        name=bot.user.display_name, icon_url=bot.user.display_avatar
    )
    bingo_rules_embed2.set_thumbnail(url=EMBED_ICON_URL)
    bingo_rules_embed2.add_field(
        name="1.",
        value="For tiles that require you to purchase something, multiple players combining points is not allowed. Example: One player must get all 1000 molch pearls to buy the fish sack. It cant be player 1 with 600, and player 2 with 400.",
        inline=False,
    )
    bingo_rules_embed2.add_field(
        name="2.",
        value="There will be challenges where you will compete live with other teams. Have fun with it. Don't be turds.",
        inline=False,
    )
    bingo_rules_embed2.add_field(
        name="3.",
        value="Tiles can only be approved for completion after they have been announced, and submitted with a timestamp after the annoucement.",
        inline=False,
    )
    bingo_rules_embed2.add_field(
        name="4.",
        value="A Pet counts as any unique for any \"Obtain\" tile. Things like 'ashes', unique bones, special teleports do not count toward uniques, unless otherwise specified.",
        inline=False,
    )

    await ctx.send(embed=bingo_rules_embed)
    await ctx.send(embed=bingo_rules_embed2)
    return

# "!bingohowto" command
# Displays the "how to submit" message
@bot.command()
async def howto(ctx):
    howto_embed = discord.Embed(
        title=f"How to Submit",
        color=0x00FFDD,
        description="Follow these instructions to post a bingo submission.",
    )
    howto_embed.set_author(name=bot.user.display_name, icon_url=bot.user.display_avatar)
    howto_embed.set_thumbnail(url=EMBED_ICON_URL)
    howto_embed.add_field(
        name="Step One",
        value="Type `!bingotasks` and find the Task # of the tile you want to submit.",
        inline=False,
    )
    howto_embed.add_field(
        name="Step Two",
        value="Type `!bingosubmit X` where `X` is the Task # you just located.",
        inline=False,
    )
    howto_embed.add_field(
        name="Step Three",
        value="Attach your screenshot(s) to the message and post.",
        inline=False,
    )
    howto_embed.add_field(
        name="Step Four",
        value="Click either 'Submit' or 'Cancel' on the confirmation window that appears.",
        inline=False,
    )
    howto_embed.add_field(
        name="Step Five",
        value="Your submission will receive a ✅ or ❌ when it is approved or denied, respectively.",
        inline=False,
    )
    howto_embed.add_field(
        name="Instructions with Pictures",
        value="[HERE](https://cdn.discordapp.com/attachments/1195577008973946890/1200208657477025813/instructions.png?ex=65c5586a&is=65b2e36a&hm=1859e3a5335352d7d44450b8ac7f1f8a97a592f2a8e64633ed28f8705c6d7374&)",
        inline=False,
    )
    

    await ctx.send(embed=howto_embed)
    return

# "!bingocredits" command
# Displays the credits, listing everyone involved in the project
@bot.command()
async def credits(ctx):
    credits_embed = discord.Embed(title=f"Credits",color=0x00FFDD)
    credits_embed.set_author(name=bot.user.display_name, icon_url=bot.user.display_avatar)
    credits_embed.set_thumbnail(url=EMBED_ICON_URL)
    credits_embed.add_field(name="Battle Bingo Created by:",value="The Bingo Snake, Foki",inline=False)
    credits_embed.add_field(name="Artwork:",value="Foki also",inline=False)
    credits_embed.add_field(name="Prize Money:",value="All of you guys and your generosity!",inline=False)

    await ctx.send(embed=credits_embed)
    return

# RESTRICTED COMMANDS

# "!bingosubmit int" command
# Tile Submition Tool
# Takes attachments from message
# allows approval by bingo admins in Discord
# int - task number
# Data about the interaction is used for recognizing submissions
@bot.command()
async def submit(ctx, task: int) -> None:

    # TODO: Is task already completed?

    team, isCaptain = await find_bingo_team(ctx.author)
    if team == None:
        await ctx.send("I'm sorry, but you do not have access to this command.")
        return

    if (
        ctx.channel.id != BINGO_TEAM_CHANNELS.get(team)
        and ctx.channel.id != TEST_SUBMISSIONS_CHANNEL
    ):
        if ctx.author.id != ADMIN_RIGHTS:
            await ctx.send("This is not your teams submissions channel!")
            return
        else:
            await ctx.send("Right away Mr. Foki sir!  o7")

    if task > (len(task_list) + 5) or task <= 0:
        await ctx.send("Task number out of bounds.")
        return

    # are there attachments on the message?
    if ctx.message.attachments:
        # are the attachments the right file types?
        for attachment in ctx.message.attachments:
            name = attachment.filename.lower()
            # parameter needs to be a tuple
            if name.endswith((".png", ".jpg", ".jpeg", ".gif")):
                continue
            else:
                await ctx.send(
                    "One of the files you have submitted has an unsupported file type.  Please use .png, .jpg, .jpeg, or .gif."
                )
                return

        # is the user SURE they want to post this?
        toPost = await post(ctx, bot, ctx.message.attachments[0].url, task)
        if not toPost:
            return

        # are there multiple images on the submission?
        if len(ctx.message.attachments) > 1:
            await ctx.send(
                "Your submission has been sent to Mr. Foki Ironman, CEO/Founder, Battle Bingo LLC. for review."
            )

            # Updating database
            await Queries.add_submission(
                task,
                ctx.message.attachments[0].url,
                ctx.message.jump_url,
                ctx.author.display_name,
                team,
                ctx.channel.id,
                ctx.message.id,
            )

            # snarky options if desired
            # bot_response = random.randint(1, 10)
            # await message.channel.send(submission_responses_dict[bot_response])

            # posting logs to #logs channel
            await submission_alert(ctx, bot, team, task, multi=True)
            # LOG
            print("Foki Bot: Captain, we've received a bingo submission.")

        # there is only one image in the submission
        else:
            await ctx.send(
                "Your submission has been sent to Mr. Foki Ironman, CEO/Founder, Battle Bingo Inc. for review."
            )

            # Updating database
            await Queries.add_submission(
                task,
                ctx.message.attachments[0].url,
                ctx.message.jump_url,
                ctx.author.display_name,
                team,
                ctx.channel.id,
                ctx.message.id,
            )

            # snarky options if desired
            # bot_response = random.randint(1, 10)
            # await message.channel.send(submission_responses_dict[bot_response])

            # posting logs to #logs channel
            await submission_alert(ctx, bot, team, task, multi=False)
            # LOG
            print("Foki Bot: Captain, we've received a bingo submission.")

    # No attachment on message
    else:
        await ctx.send(
            "There was no attachment on that post. Your submission has been rejected."
        )
    return


"""
Creates embed of all current submissions for admin approval
"""


# "!bingoapprove" command
# For approving submissions
# ADMIN USE ONLY
@bot.command()
async def approve(ctx) -> None:
    if ctx.author.id not in ADMIN_RIGHTS:
        await ctx.send("You are not authorized to use this command.")
        return
    if (
        ctx.channel.id != BINGO_LOGS_CHANNEL
        and ctx.channel.id != TEST_SUBMISSIONS_CHANNEL
    ):
        await ctx.send("This command is not authorized for use in this channel.")
        return

    # submissions is a LIST of RECORDS
    submissions = await Queries.get_submissions()

    view = ApproveTasks(ctx, bot)
    view.data = submissions

    await view.send(ctx)
    return


# "!bingorange" command
# Updates the amount of tasks available
# start - first task in range
# end - last task in range
@bot.command()
async def range(ctx, start: int, stop: int):
    if ctx.author.id not in ADMIN_RIGHTS:
        await ctx.send("You are not authorized to use this command.")
        return
    await Queries.update_unlocked_tasks(start, stop)
    return


# "!bingoquit" command
# Closes the bot
@bot.command()
async def quit(ctx) -> None:
    if ctx.author.id not in ADMIN_RIGHTS:
        await ctx.send("Nice try, but no robot murder happening today.")
        return
    await ctx.send("Powering down. Later nerds.")
    await wom_client.close()
    print("Wise Old Man connection closed.")
    await asyncio.sleep(1.0)  # to prevent unclosed connector? in the future
    await bot.close()
    print("Bot powered down.")
    return


#
# DISCORD API CODE
#

"""
Static Discord bot event, triggers whenever bot finishes booting up.
"""


@bot.event
async def on_ready():
    # LOG
    print("{0.user.display_name}: Captain, warp drive is online.".format(bot))
    await wom_client.start()

    # Custom discord announcement
    #await bot.get_channel(BINGO_GENERAL_CHANNEL).send("Bingo has officially begun!  Good luck competitors!")


"""
Static Discord bot event, triggers whenever a message is sent by a user.
"""


@bot.event
async def on_message(message):
    # TODO: if message NOT IN these channels:
    await bot.process_commands(message)

    # TFK BABY LFG
    # emoji = "<:tfk2:1199460856182878240>"
    # await message.add_reaction(emoji)

    if message.author.id == 483092611419078659:
        await message.add_reaction("🖕")

    # Tells bot to ignore its own messages
    if message.author == bot.user:
        return


# Runs the bot
bot.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)

# FUTURE IDEAS

# - show board command
# - show current board state?

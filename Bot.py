from typing import Tuple
import discord
from discord.ext import commands
import random
import logging
import datetime
import os
from dotenv import load_dotenv
load_dotenv(override=True)
import wom
from wom import CompetitionStatus
from Tasks import Tasks
from ApproveTasks import ApproveTasks
from Data import *
import Queries

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
# DISCORD TEAM ROLES (IDS: NAMES)
GENERAL_BINGO_ROLE = 1196183580615909446
BINGO_TEAM_ROLES = {
    1196180292742951003: "The Fat Woodcocks",
    1196182424913199217: "The Posture Inspectors",
    1196182816099152013: "TFK",
    1196183381931720796: "The Real World Traders",
    1196183533308358696: "BBBBB",
    1196916756384600074: "Phased and Confused",
    # For testing
    1195556259160666172: "Team Test",
}
BINGO_TEAM_CHANNELS = {
    "The Fat Woodcocks": 1197945391929368596,
    "The Posture Inspectors": 1197945547714207805,
    "TFK": 1197945883585675354,
    "The Real World Traders": 1197946038179352696,
    "BBBBB": 1197946114356289587,
    "Phased and Confused": 1197946234384691301,
}
CAPTAIN_ROLE = 1195584494636384321
# foki, me
ADMIN_RIGHTS = [453652490274078720, 545728431917236226]
# ADMIN_RIGHTS = [545728431917236226]
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

# MISC
tasks_revealed = 9

#
# BOT COMMANDS
#

# TODO: memory leak??
# TODO: outside hosting?

# TODO: IMPORTANT--prevent double submissions
# TODO: SAVE THE DATA!! reboot from save command?  save data manually command?
# TODO: submit multiple photos at once
# TODO: "who called what" command logs?
# TODO: divide code into packaged files
# TODO: write bot start-up batch script
# TODO: match team color to profile embed, or random colors
# TODO: add toggleable options
# TODO: convert all images to discord.File local images
# TODO: docker?

# "!bingotest" command
# For testing purposes
@bot.command()
async def test(ctx) -> None:
    
    pass


# GLOBAL COMMANDS


# "!bingowhen" command
# Ping pong
@bot.command()
async def when(ctx) -> None:
    await ctx.channel.send("👀")
    return


# "!bingoquit" command
# Closes the bot
@bot.command()
async def quit(ctx) -> None:
    await ctx.send("Powering down.  Later nerds.")
    await wom_client.close()
    print("Wise Old Man connection closed.")
    await bot.close()
    print("Bot powered down.")
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
        value="Thursday, January 25th, 9:30pm\nafter the clan meeting",
    )
    bingo_info_embed.add_field(name="Duration:", value="3 weeks")
    bingo_info_embed.add_field(name="Cost to Enter:", value="10M GP per person")
    bingo_info_embed.add_field(name="", value="", inline=False)
    bingo_info_embed.add_field(name="Current prize pool:", value="Over 1 Billion GP")
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
    bingo_info_embed.add_field(name="The Posture Inspectors", value="Captain: Seczey")
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
# TODO: Track amount of posts in general channel as smack talk stat
@bot.command()
async def me(ctx) -> None:
    global player_titles_dict

    # Getting member and if they're a captain
    team, isCaptain = await find_bingo_team(ctx.author)
    if team == None:
        await ctx.channel.send(
            "You are not in the bingo.  But it's not too late to sign up!"
        )
        return
    elif team == "Bingo":
        team = "Bingo Participant"
    # Player custom title
    title = player_titles_dict.get(random.randint(1, len(player_titles_dict)))
    # Player custom smack_talk/quote
    smack_talk = get_smack_talk(team)
    gained = await wise_old_man(ctx)
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
# TODO: Trim these town to all unlocked tasks
# done
@bot.command()
async def DISABLEDtasks(ctx) -> None:
    view = Tasks(ctx.author)
    view.data = list(task_list.values())

    await view.send(ctx)
    return


# "!bingomenu" command
# Displays the bingo menu command
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
    bingo_info_embed.add_field(name="!bingomenu", value="This menu.")
    bingo_info_embed.add_field(
        name="!bingoinfo", value="Information about the bingo event."
    )
    bingo_info_embed.add_field(name="!bingome", value="Your bingo player card.")
    bingo_info_embed.add_field(name="", value="", inline=False)
    bingo_info_embed.add_field(name="!bingorules", value="The official bingo rules.")
    bingo_info_embed.add_field(name="!bingowhen", value="Ping pong.")
    bingo_info_embed.add_field(
        name="!bingotasks",
        value="DISABLED UNTIL BINGO START\nShows a list of all currently available bingo tasks.",
    )
    bingo_info_embed.add_field(name="", value="", inline=False)
    bingo_info_embed.add_field(
        name="!bingosubmit",
        value="UNDER CONSTRUCTION DO NOT USE\nTile Submission Tool, used to submit your tile completion screenshots.",
    )
    bingo_info_embed.add_field(
        name="!bingoapprove",
        value="ADMIN USE ONLY.  Approve submissions.",
    )

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


# CHANNEL SPECIFIC COMMANDS


# "!bingosubmit int" command
# Tile Submition Tool
# Takes attachments from message, sends to Google Doc for verification
# int - task number
# Data about the interaction is used for recognizing submissions
@bot.command()
async def submit(ctx, task: int) -> None:

    # TODO: IMPORTANT---switch before going live
    # TODO: Check for submission in correct team channel
    # TODO: Is task already completed?

    team, isCaptain = await find_bingo_team(ctx.author)
    if team == None:
        await ctx.send("I'm sorry, but you do not have access to this command.")
        return

    if ctx.channel.id != BINGO_TEAM_CHANNELS.get(team):
        await ctx.send("This is not your teams submissions channel!")
        return
    
    if task > len(task_list) or task <= 0:
        await ctx.send("Task number out of bounds.")
        return
        
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if attachment.filename.endswith((".png", ".jpg", ".jpeg", ".gif")):

                # Confirmation window
                toPost = await post(ctx, attachment.url, task)
                if not toPost:
                    return

                await ctx.send(
                    "Your submission has been sent to Bingo Overlord Foki for review."
                )

                # Updating database
                await Queries.add_submission(
                    task,
                    attachment.url,
                    ctx.author.display_name,
                    team,
                    ctx.channel.id,
                    ctx.message.id,
                )

                # snarky options if desired
                # bot_response = random.randint(1, 10)
                # await message.channel.send(submission_responses_dict[bot_response])

                # posting logs to #logs channel
                await submission_alert(ctx, team)
                # LOG
                print("Foki Bot: Captain, we've received a bingo submission.")

            # Submission screenshot is the wrong file type
            else:
                await ctx.send(
                    "The file type you have submitted is not supported.  Please use .png, .jpg, .jpeg, or .gif."
                )

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
# TODO: add admin specific logic
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


#
# HELPER FUNCTIONS
#

"""
Posts embed message to specific Discord channel with submission information
message - Discord message object
id - Submission UUID
BINGO_LOGS_CHANNEL - Discord channel to post message to (channel ID)
"""


# done
async def submission_alert(ctx, team: str) -> None:
    d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # TODO: IMPORTANT---Switch to proper LOGS channel at launch
    channel = await bot.fetch_channel(BINGO_LOGS_CHANNEL)

    submission_embed = discord.Embed(
        title=f"Submission Received", url=ctx.message.jump_url, color=0x0000FF
    )
    submission_embed.set_thumbnail(url=ctx.message.attachments[0].url)
    submission_embed.add_field(name="Team:", value=team)
    submission_embed.add_field(name="Player:", value=ctx.author.display_name)
    submission_embed.add_field(name="Approved on:", value=d)

    # Posting embed the custom embed
    await channel.send(embed=submission_embed)


"""
Figure out what bingo team the command caller is on
user - player
BINGO_TEAM_ROLES - map of message id - bingo team names (string)
Cycle through all bingo teams, if user has role, return team name.
"""


# done
async def find_bingo_team(user) -> Tuple[str, str]:
    isCaptain = False
    isBingo = False
    roles = user.roles

    for i in roles:
        if i.id == CAPTAIN_ROLE:
            isCaptain = True
        elif i.id == GENERAL_BINGO_ROLE:
            isBingo = True

    for key in BINGO_TEAM_ROLES.keys():
        for role in roles:
            if key == role.id:
                # Returning team/captain?
                return BINGO_TEAM_ROLES.get(key), isCaptain
    if isBingo:
        return "Bingo", None

    return None, None


# done
"""
Gets smack talk from a dict of hardcoded entries, directed at random team.
Choose random team, pass team through hardcoded dict, return finalized string.
TODO: I do not like how this is coded.  Is there a better way?
"""
LIST_SIZE = 42


# done
def get_smack_talk(teamIn: str) -> str:
    global BINGO_TEAM_ROLES

    team = "Team Test"
    while team == "Team Test" and team != teamIn:
        team = random.choice(list(BINGO_TEAM_ROLES.values()))

    player_smack_talk = {
        1: f"{team} doesn't stand a chance!",
        2: f"Are you sure {team} is playing the right bingo?  It seems like they took a wrong turn on the way to mediocrity.",
        3: f"{team}'s strategy is so outdated; it's like playing chess against a team of checkers enthusiasts.",
        4: f"I'm not sure what {team}'s problem is, but I'd be willing to be that it's something hard to pronounce.",
        5: f"Brains aren't everything.  And in {team}'s case, they're nothing.",
        6: f"I wouldn't be surprised if {team} practiced losing instead of winning.",
        7: f"I'd smack talk {team}, but then I'll have to explain it afterwards, so never mind.",
        8: f"I thought of {team} today. It reminded me to take out the trash.",
        9: f"I've seen faster moves in a chess game played by a sloth. Is this your idea of a winning strategy?",
        10: f"{team} is like playing against an opponent from Wish.com",
        11: f"I hope {team} has a backup plan, because Plan A clearly isn't working.",
        12: f"I heard {team}'s strategy is to rely on luck.",
        13: f"I hope {team} enjoys the view from the bottom.",
        14: f"I'd wish {team} good luck, but let's be honest - they're going to need more than luck to survive.",
        15: f"Goals swift as the wind, Defeat echoes in each cheer, Victory is ours.",
        16: f"There once was a team full of pride, {team}. On Gielinor, they couldn't hide. But the tiles came a-knockin', Their dreams left a-rockin', In defeat, their hopes took a slide.",
        17: f"Maybe we should donate a few team members to {team} to help them out...",
        18: f"{team} who?",
        19: f"I bet {team} eats boneless wings.",
        20: f"{team} must play RS3.",
        21: f"Uh ... {team}'s gonna need more people.",
        22: f"{team} are legit bad.",
        23: f"I wonder if {team} are actually trying.",
        24: f"My mom thinks {team} are trying really hard.",
        25: f"Sit {team}.",
        26: f"{team} has two brain cells and they are fighting for third place",
        27: f"{team} are the reason the gene pool needs a lifeguard.",
        28: f"Maybe {team} should take up checkers.",
        29: f"Is {team}'s strategy to get as far behind as possible?",
        30: f"Do I really need to insult {team} more? Just look at them.",
        31: f"Bless {team}'s heart.",
        32: f"It's cute how much {team} are trying.",
        33: f"If a team were the human equivalent of a participation trophy, it would be {team}.",
        34: f"My days of not taking {team} seriously have come to a continue not taking them seriously.",
        35: f"They have their entire life to relax, not sure why {team} decided to do it during bingo.",
        36: f"{team} are a group of goblins.",
        37: f"Maybe {team} should try something more their speed, like a group ironman.",
        38: f"{team} can't even count to yellow.",
        39: f"I really appreciate {team}. They make me feel like we don't have to try as hard.",
        40: f"The closest {team} comes to a brainstorm is a light drizzle.",
        41: f"I wonder if Baldy is actually playing for {team}...",
        42: f"I feel bad. The only thing {team} will get for this performance is a clan credit.",
    }
    talk = random.randint(1, len(player_smack_talk))
    return player_smack_talk.get(talk)


"""
Creates task submission UI for verification
icon - url of the embed thumbnail
task - int task number
Creates embed with task submission info, asks for verification.  Submit returns true, cancel returns false.
"""


# done
async def post(ctx, url: str, task: int):
    bingo_submit_embed = discord.Embed(
        title=f"Verify Task Submission",
        color=0x00FFDD,
    )
    bingo_submit_embed.set_author(
        name=bot.user.display_name, icon_url=bot.user.display_avatar
    )
    bingo_submit_embed.set_thumbnail(url=url)
    bingo_submit_embed.add_field(name=f"Task #{task}", value=task_list.get(task))

    class SubmitButton(discord.ui.View):
        submitPost = False

        @discord.ui.button(
            label="Submit", custom_id="submit", style=discord.ButtonStyle.green
        )
        async def submit(self, interaction, button) -> None:
            self.submitPost = True
            await interaction.response.defer()

        @discord.ui.button(
            label="Cancel", custom_id="cancel", style=discord.ButtonStyle.red
        )
        async def cancel(self, interaction, button) -> None:
            await interaction.response.defer()

    view = SubmitButton()

    are_you_sure = await ctx.send(
        "Are you sure this is the task you want to submit?",
        embed=bingo_submit_embed,
        view=view,
        ephemeral=True,
    )
    await bot.wait_for("interaction")
    await are_you_sure.delete()
    return view.submitPost


"""
Connects to WOM API and gets competition data.
Returns player XP gained during competition.
"""


# done
async def wise_old_man(ctx):
    wom_client.set_user_agent("@kyanize.")

    # LOG
    print("Foki Bot: Captain, incoming transmission from Wise Old Man.")

    result = await wom_client.players.get_competition_standings(
        ctx.author.display_name, CompetitionStatus.Ongoing
    )
    if result.is_ok:
        result = result.to_dict()
        if len(result.get("value")) == 0:
            gained = "Not currently available."
        else:
            gained = result.get("value")[0].get("progress").get("gained")
    else:
        gained = "Not currently available."

    return gained


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
    return

    # Custom discord announcement
    # await bot.get_channel(BINGO_GENERAL_CHANNEL).send("Fuck you back Sasa.")


"""
Static Discord bot event, triggers whenever a message is sent by a user.
"""


@bot.event
async def on_message(message):
    # TODO: if message NOT IN these channels:
    await bot.process_commands(message)

    if message.author.id == 483092611419078659:
        await message.add_reaction("🖕")

    # Tells bot to ignore its own messages
    if message.author == bot.user:
        return

    team, isCaptain = await find_bingo_team(message.author)

    if team == "None":
        return

    if message.channel.id == BINGO_LOGS_CHANNEL:
        if message.content == "ping":
            await message.channel.send("pong")
            return
        # Bot responds to commands sent from Google API via Webhook


"""
    if message.channel == client.get_channel(TEST_SUBMISSIONS_CHANNEL):
        ### bingosubmit command
        if cmd == "submit":
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.filename.endswith(
                        (".png", ".jpg", "jpeg", "gif")
                    ):
                        num_submissions += 1
                        id = str(uuid.uuid4())

                        map_of_submissions[id] = message

                        # posting to google sheets
                        await post_bingo_submission(attachment.url, id)

                        # posting to #posthere channel
                        await message.channel.send(
                            "Your submission has been successfully submitted to the Bingo council."
                        )

                        # snarky options if desired
                        # bot_response = random.randint(1, 10)
                        # await message.channel.send(submission_responses_dict[bot_response])

                        # posting logs to #logs channel

                    # wrong file type
                    else:
                        await message.channel.send(
                            "The file type you have submitted is not supported.  Please use .png, .jpg, .jpeg, or .gif."
                        )

            # no attachment on message
            else:
                await message.channel.send(
                    "There was no attachment on that post. Your submission has been rejected."
                )
"""

# Runs the bot
bot.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)

# FUTURE IDEAS

# - show board command
# - show teams command
# - show current board state?

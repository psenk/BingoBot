import wom
import datetime
import random
import discord
from Data import *
from MiniView import MiniView

TZ_OFFSET = -6.0
BINGO_LOGS_CHANNEL = 1195530905398284348
#foki, me
ADMIN_RIGHTS = [453652490274078720] # 545728431917236226
CAPTAIN_ROLE = 1195584494636384321
GENERAL_BINGO_ROLE = 1196183580615909446
# DISCORD TEAM ROLES (IDS: NAMES)
BINGO_TEAM_ROLES = {
    1196180292742951003: "The Fat Woodcocks",
    1196182424913199217: "Seczey\'s Revenge",
    1196182816099152013: "TFK",
    1196183381931720796: "The Real World Traders",
    1196183533308358696: "BBBBB",
    1196916756384600074: "Phased and Confused",
    # For testing
    # 1195556259160666172: "Team Test",
}

tz_info = datetime.timezone(datetime.timedelta(hours=TZ_OFFSET))



#
# HELPER FUNCTIONS
#

"""
Posts embed message to specific Discord channel with submission information
message - Discord message object
id - Submission UUID
BINGO_LOGS_CHANNEL - Discord channel to post message to (channel ID)
"""

async def submission_alert(ctx, bot, team: str, task: int, multi: bool = False) -> None:
    d = datetime.datetime.now(tz_info).strftime("%Y-%m-%d %H:%M:%S")
    # TODO: IMPORTANT---Switch to proper LOGS channel at launch
    channel = await bot.fetch_channel(BINGO_LOGS_CHANNEL)

    if (multi):
        submission_embed = discord.Embed(
            title=f"Submission Received (multiple images)", url=ctx.message.jump_url, color=0x0000FF
        )
    else:
        submission_embed = discord.Embed(
            title=f"Submission Received", url=ctx.message.jump_url, color=0x0000FF
        )
    submission_embed.set_thumbnail(url=ctx.message.attachments[0].url)
    submission_embed.add_field(name="Team:", value=team)
    submission_embed.add_field(name="Player:", value=ctx.author.display_name)
    submission_embed.add_field(name="Task ID:", value=task)
    if len(task_list) <= task <= len(task_list) + 5:
        submission_embed.add_field(name="Task:", value=bonus_tasks.get(task))
    else:
        submission_embed.add_field(name="Task:", value=task_list.get(task))
    submission_embed.add_field(name="Submitted on:", value=d)

    # Posting embed the custom embed and custom view (buttons)
    view = MiniView(channel, ctx.author, team, task, ctx.message)
    view.message = await channel.send(embed=submission_embed, view=view)
    
"""
Figure out what bingo team the command caller is on
user - player
BINGO_TEAM_ROLES - map of message id - bingo team names (string)
Cycle through all bingo teams, if user has role, return team name.
"""

async def find_bingo_team(user):
    isCaptain = False
    isBingo = False
    roles = user.roles
    
    if user.id in ADMIN_RIGHTS:
        return "Admin", None

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

"""
Gets smack talk from a dict of hardcoded entries, directed at random team.
Choose random team, pass team through hardcoded dict, return finalized string.
TODO: I do not like how this is coded.  Is there a better way?
"""
LIST_SIZE = 42

def get_smack_talk(teamIn: str) -> str:
    global BINGO_TEAM_ROLES

    team = teamIn
    while team == teamIn:
        team = random.choice(list(BINGO_TEAM_ROLES.values()))

    player_smack_talk = {
        1: f"{team} doesn't stand a chance!",
        2: f"Are you sure {team} is playing the right bingo?  It seems like they took a wrong turn on the way to mediocrity.",
        3: f"{team}'s strategy is so outdated; it's like playing chess against a team of checkers enthusiasts.",
        4: f"I'm not sure what {team}'s problem is, but I'd be willing to bet that it's something hard to pronounce.",
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


async def post(ctx, bot, url: str, task: int):
    bingo_submit_embed = discord.Embed(
        title=f"Verify Task Submission",
        color=0x00FFDD,
    )
    bingo_submit_embed.set_author(
        name=bot.user.display_name, icon_url=bot.user.display_avatar
    )
    bingo_submit_embed.set_thumbnail(url=url)
    if len(task_list) <= task <= (len(task_list) + 5):
            bingo_submit_embed.add_field(name=f"Task # {task}", value=bonus_tasks.get(task), inline=False)
    else:
        bingo_submit_embed.add_field(name=f"Task # {task}", value=task_list.get(task), inline=False)

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
async def wise_old_man(ctx, client):
    client.set_user_agent("@kyanize.")

    # LOG
    print("Foki Bot: Captain, incoming transmission from Wise Old Man.")

    result = await client.players.get_competition_standings(
        ctx.author.display_name, wom.CompetitionStatus.Ongoing
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


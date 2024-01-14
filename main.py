import discord
from discord.ext import commands
from discord.ui import View
import random
import logging
import datetime
import os
import gspread
from dotenv import load_dotenv

load_dotenv()
from google.oauth2 import service_account
from googleapiclient.discovery import build
import uuid

#
# CONSTANTS
#

# AUTH
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_DOCS_KEY = os.getenv("GOOGLE_DOCS_KEY")
# TEST CHANNELS & WEBHOOKS
# Logic's Server
TEST_SUBMISSIONS_CHANNEL = 1194832130962890842
BINGO_TEST_CHANNEL = 1194488938480537740
TEST_WEBHOOK_USER_ID = 1194889597738549298
# LIVE CHANNELS & WEBHOOKS
BINGO_GENERAL_CHANNEL = 1193039460980502578
BINGO_TEST_CHANNEL = 1195530905398284348
# BINGO_SUBMISSIONS_CHANNEL =
# BINGO_WEBHOOK_USER_ID =
# DISCORD TEAM ROLES (IDS: NAMES)
BINGO_TEAM_ROLES = {
    1195523300277895189: "Terrible Trouncers",
    1195523386621825177: "Bodacious Bouncers",
    1195523436685049897: "Pernicious Pouncers",
    1195523498299371570: "Amazing Announcers",
    1195523607384834060: "Relaxing Renouncers",
    # For testing
    1195556259160666172: "Test",
}
CAPTAIN_ROLE = 1195584494636384321
# URLs & MESSAGES
EMBED_ICON_URL = "https://shorturl.at/wGOXY"
RULES_POST_URL = "https://discord.com/channels/741153043776667658/1193039460980502578/1193042254751879218"
RULES_POST_MSG = 1193042254751879218

#
# VARIABLES
#

# DISCORD AUTH
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="!bingo", intents=intents)
# client = commands.Bot(command_prefix=commands.when_mentined_or('!'))
# TEST
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

# MAPS
map_of_submissions = {}
map_of_embeds = {}
map_of_embed_messages = {}

# CUSTOMIZATION
submission_responses = {
    1: "DID YOU REMEMBER YOUR CODEWORD?",
    2: "REALLY? THIS IS YOUR SUBMISSION? ARE YOU SURE?",
    3: "YOU'RE THE FIRST PERSON TO SUBMIT THIS! PROBABLY. MAYBE.",
    4: "ABOUT TIME.",
    5: "FINALLY!",
    6: "ARE YOU WAITING FOR A TIP? GO AWAY.",
    7: "CONGRATS [USER] FOR YOUR DROP/ACHIEVEMENT/THING!",
    8: "FOKI ALREADY HAS ONE OF THESE, SO...",
    9: "TOOK YA LONG ENOUGH!",
    10: "FUCK YOU DJ",
}
# Gives user profiles custom titles
player_titles_dict = {
    1: "Formidable",
    2: "Green",
    3: "Monumental",
    4: "Smelly",
    5: "Courageous",
    6: "Mean Bean",
    7: "Crafty",
    8: "Humble",
    9: "Terrible",
    10: "Vile",
    11: "Despicable",
    12: "Sinister",
    13: "Malevolent",
    14: "Nasty",
    15: "Wretched",
    16: "Gruesome",
    17: "Cruel",
    18: "Abominable",
    19: "Diabolical",
    20: "Fiendish",
    21: "Wise",
    22: "Fearless",
    23: "Radiant",
    24: "Agile",
    25: "Mysterious",
    26: "Charming",
    27: "Dynamic",
    28: "Tranquil",
    29: "Bold",
    30: "Melodious",
    31: "Mystical",
    32: "Daring",
    33: "Luminous",
    34: "Swift",
    35: "Enigmatic",
    36: "Charismatic",
    37: "Spirited",
    38: "Serene",
    39: "Audacious",
    40: "Harmonious",
    41: "Sweaty",
    42: "Fine",
    43: "Bold",
    44: "Snake",
    45: "Strategic",
    46: "Tactical",
    47: "Agile",
    48: "Skilled",
    49: "Adaptable",
    50: "Precise",
    51: "Quick-thinking",
    52: "Persistent",
    53: "Competitive",
    54: "Resourceful",
    55: "Alert",
    56: "Focused",
    57: "Clever",
    58: "Tenacious",
    59: "Efficient",
    60: "Coordinated",
    61: "Versatile",
    62: "Inventive",
    63: "Adept",
    64: "Intuitive",
    65: "Spoon",
}

# Dict of bingo tasks
task_list = {
    1: "[5 points] Most cumulative beer brought during all task completions",
    2: "[2 points] Receive a non-prayer scroll purple unique from Chambers of Xeric (Buckler, DHCB, Dinh's, Ancestral, Dragon Claws, Elder Maul, Kodai, Twisted Bow, Kit, Dust, Pet)",
    3: "[3 points] Obtain an Enhanced Crystal Weapon Seed",
    4: "[2 points] Achieve 5,000,000 Woodcutting XP AND obtain a Fox Whistle",
    5: "[3 points] Obtain all pieces to complete a Voidwaker",
    6: "[1 point] Obtain a Warped sceptre",
    7: "[1 point] Achieve 125,000 xp/hr for a minimum of 60 minutes while mining",
    8: "[1 point] Obtain a Dark Bow",
    9: "[1 point] Obtain an Ash covered tome from Petrified Pete's Ore Shop",
    10: "[3 points] Obtain one of three Visages (Skeletal, Wyvern, or Draconic)",
    11: "[5 points] Last the longest, while still killing the Corrupted Hunleff (Must loot chest after)",
    12: "[2 points] Receive a purple unique from Theatre of Blood (Avernic defender hilt, Justicar, Rapier, Sanguinesti, Scythe, Kit, Dust, Pet)",
    13: "[1 point] Alch the purple you received (one time use)",
    14: "[2 points] Complete Chambers solo in under 17 minutes, trio under 14:30, or any other team size under 12:30.",
    15: "[3 points] Receive an imbued heart, dust battlestaff, mist battlestaff, or eternal gem from a Superior",
    16: "[3 points] Obtain a drop from the Mega-rare table from a master clue",
    17: "[2 points] Obtain an Abyssal Lantern and Abyssal Needle",
    18: "[1 point] Obtain an Occult Necklace",
    19: "[2 points] Obtain all of the wilderness rings",
    20: "[2 points] Complete a Grandmaster quest",
    21: "[5 points] Earn a Fire cape before anyone else",
    22: "[1 point] Score a goal in gnomeball against an opposing bingo team",
    23: "[2 points] Obtian a Revenant Weapon (Viggora's Chainmace, Craw's Bow, or Thammaron's Sceptre)",
    24: "[2 points] Receive a good purple unique from Tombs of Amascut (Masori, Fang, Shadow, Pet)",
    25: '[3 points] Obtain the following: Bandos Chestplate, Armadyl Chainskirt, Zamorak Spear, Armadyl Crossbow, Zaryte Vambraces. Then wear this outfit and screenshot saying "I am the God this dungeon was named after." (have other weapon in inventory while not wearing)',
    26: "[2 points] Obtain a Slepey Tabley and any Nightmare Unique (Staff, Inquisitor, Orb, Pet, Jar, Egg)",
    27: "[2 points] Obtain a Hydra Claw or Hydra Leather",
    28: "[1 point] Successfully bake a Wild Pie. Ironman style. (Gather all ingredients, and successful process.)",
    29: "[1 point] Obtain a Pharaoh's Sceptre from Pyramid Plunder",
    30: "[2 points] Obtain a unique from Zalcano (Crystal tool seed, Zalcano shard, pet, onyx)",
    31: '[5 points] Least deaths wins. Nominate your Champion. "PK" opposing teams while completing ToB. One point goes to the team whos member has the least deaths',
    32: "[3 points] Achieve the highest level invocation Tombs of Amascut completion in any scale",
    33: "[3 points] Obtain a Sigil, Jar, or Pet from Corp",
    34: "[3 points] Obtain any vestige from one of the Desert Treasure II bosses",
    35: "[2 points] Obtain an Eternal Glory",
    36: "[1 point] Kill 10 different quest bosses",
    37: "[1 point] Receive an 84,000 thieving experience drop",
    38: "[2 points] Complete a heavy ballista",
    39: "[1 point] Create an Amulet of Torture, Ironman style",
    40: "[2 points] Obtain Dragon limbs",
    41: "[5 points] Earn an Infernal cape before anyone else",
    42: "[3 points] Achieve the most valuable Bounty Hunter PK (cannot be boosted/friends/clan/etc.)",
    43: "[1 point] Obtain a crystal from Cerberus (Eternal, Pegasian, Primordial)",
    44: "[2 points] Obtain a non-head unique from Vorkath (Dragonbone necklace, Jar, pet, either visage) ((asking about wrath talisman loses your team 1 point))",
    45: "[1 point] Obtain Bryophyta's Essence",
    46: "[2 points] Obtain a Nex Unique (Hilt, Vambs, Torva, Horn, Pet) (I will allow vambs if you already got them from the God of the Dungeon tile)",
    47: "[1 point] Kill Giant Mole 500 times",
    48: "[1 point] Obtain all four rings from Dagannoth Kings",
    49: "[2 points] Purchase 10000+ sharks from minnows in a single transaction",
    50: "[1 point] Catch a Lucky Impling",
    51: "[5 points] Win a game of Connect-Four against another team's member",
    52: '[3 points] Earn the title: "of a Thousand Hunts". Catch 1000 Salamanders, 1000 Chins, 1000 Implings, and 1000 Herbiboar.',
    53: '[5 points] Have 3 people from your team earn an Infernal cape (if you got a kc during the "earn a cape before anyone else" tile, I will count that too)',
    54: "[2 points] Obtain a fang and a visage from Zulrah",
    55: "[1 point] Obtain a Granite thing from Grotesque Guardians (except dust)",
    56: "[2 points] Obtain a double item chest from Barrows, or finish a full set for one brother",
    57: "[3 points] Receive a Dragon Full Helm as a drop",
    58: "[1 point] Obtain a Sarachnis cudgel",
    59: "[1 point] Receive a Blood Shard as a drop (Thieving or Killing Vyrewatch)",
    60: "[1 point] Obtain an Earth Warrior Champion's Scroll",
    61: "[5 points] Achieve the largest XP drop out of any other team (Must show up as a single XP drop to count)",
    62: "[3 points] Best fashionscape (Foki is judge) (Submit all screenshots anonymously from team captain with no identifiable info)",
    63: "[3 points] Make your Torva bloody. (if you already have blood torva, screenshot new kcs.)",
    64: "[1 point] Kill the King Black Dragon without wearing or equipping anything",
    65: "[2 points] Kill all five God Wars bosses in a single inventory without banking or leaving the God Wars Dungeon",
    66: "[1 point] Obtain an Abyssal Whip",
    67: "[1 points] Obtain a master wand from the mage training arena",
    68: "[5 points] Win a game of Castle Wars against another competing team",
    69: "[3 points] Obtain a Dragon Warhammer",
    70: "[3 points] Obtain full Virtus",
    71: "[1 point] Obtain a Skotizo unique (claw, pet, onyx, Jar) ",
    72: "[2 points] Turn Amy into a Sellout. Buy one of everything from the Mahogany Homes Reward Shop",
    73: "[1 point] Obtain an Unsired",
    74: "[1 point] Obtain a Trident of the seas, and a Kraken tentacle",
    75: "[5 points] Achieve the most consecutive LMS wins. (Screenshots of each win with kc is required)",
    76: "[1 point] Obtain a Venator Shard",
    77: "[3 points] Complete a deathless, 5-man ToB with a maximum of 1 person from each bingo team",
    78: "[1 point] Obtain a Kalphite Queen uniqe (Tattered head, Dragon pickaxe, pet, jar, dragon chainbody)",
    79: "[1 point] Obtain a black mask",
    80: "[1 point] Create a sword in Giant's Foundry with a score of 69",
    81: "[1 point] Purchase the full Brimhaven Agility Arena Graceful recolour",
    82: "[5 points] Most gp earned in 1 hour on a fresh lvl 3 FTP ironman - final screenshot must include time played and be less than 60 mintues",
    83: "[3 points] Kill Duke Sucellus with the least valuable setup",
    84: "[1 point] Complete a sled run in Goblin Village with a time of 0:50 or less",
    85: "[1 point] Obtain a bunch of stuff from Chaos Archeologist. (Rcb, Fedora, Odium Shard, Malediction Shard)",
    86: "[1 point] Achieve Diamond time for the Earnest the Chicken quest speedrun",
    87: "[3 points] Equip the highest combined defense and attack bonus out of any team while on Entrana. (Will add up the two highest + bonuses)",
    88: "[1 point] Kill the bunny in Priffdinas",
    89: "[1 point] Obtain a full set of Chaos Druid robes",
    90: "[1 point] Achieve a Hallowed Sepulchre (all 5 floors) time of 6:20 or better",
    91: "[1 point] Obtain a Clue in a Bottle of every type simultaneously (all five tiers)",
    92: "[1 point] BONUS: Get a skilling pet",
    93: "[1 point] BONUS: Get a boss pet",
    94: "[1 point] BONUS: Get a 99",
    95: "[1 point] BONUS: PK over 100m to someone not in clan, not in deathmatch. Just a good ol fashioned wildy PK.",
    96: '[1 point] BONUS: Get sasa to say "I love you"',
}

# Dict of bingo task point values
task_points = {
    1: 5,
    2: 2,
    3: 3,
    4: 2,
    5: 3,
    6: 1,
    7: 1,
    8: 1,
    9: 1,
    10: 3,
    11: 5,
    12: 2,
    13: 1,
    14: 2,
    15: 3,
    16: 3,
    17: 2,
    18: 1,
    19: 2,
    20: 2,
    21: 5,
    22: 1,
    23: 2,
    24: 2,
    25: 3,
    26: 2,
    27: 2,
    28: 1,
    29: 1,
    30: 2,
    31: 5,
    32: 3,
    33: 3,
    34: 3,
    35: 2,
    36: 1,
    37: 1,
    38: 2,
    39: 1,
    40: 2,
    41: 5,
    42: 3,
    43: 1,
    44: 2,
    45: 1,
    46: 2,
    47: 1,
    48: 1,
    49: 2,
    50: 1,
    51: 5,
    52: 3,
    53: 5,
    54: 2,
    55: 1,
    56: 2,
    57: 3,
    58: 1,
    59: 1,
    60: 1,
    61: 5,
    62: 3,
    63: 3,
    64: 1,
    65: 2,
    66: 1,
    67: 1,
    68: 5,
    69: 3,
    70: 3,
    71: 1,
    72: 2,
    73: 1,
    74: 1,
    75: 5,
    76: 1,
    77: 3,
    78: 1,
    79: 1,
    80: 1,
    81: 1,
    82: 5,
    83: 3,
    84: 1,
    85: 1,
    86: 1,
    87: 3,
    88: 1,
    89: 1,
    90: 1,
    91: 1,
    92: 1,
    93: 1,
    94: 1,
    95: 1,
    96: 1,
}

# MISC

#
# BOT COMMANDS
#

# TODO: memory leak??
# TODO: outside hosting?

# TODO: IMPORTANT--prevent double submissions
# TODO: SAVE THE DATA!! reboot from save command?  save data manually command?
# TODO: submit multiple photos at once
# TODO: "who called what" command logs?
# TODO: Google API - HTML template
# TODO: divide code into packaged files
# TODO: write bot start-up batch script
# TODO: match team color to profile embed, or random colors
# TODO: add toggleable options

# GLOBAL COMMANDS

# "!bingowhen" command
# Ping pong
# TESTED GOOD
@bot.command()
async def when(ctx):
    await ctx.channel.send("👀")
    return

# "!bingoinfo" command
# Displays information about the bingo event
# TESTED GOOD
@bot.command()
async def info(ctx):
    bingo_info_embed = discord.Embed(
        title=f"Battle Bingo Information", url=RULES_POST_URL, color=0xFF0000
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
    bingo_info_embed.add_field(name="Team One", value="Captain: ")
    bingo_info_embed.add_field(name="Team Two", value="Captain: ")
    bingo_info_embed.add_field(name="", value="")
    bingo_info_embed.add_field(name="Team Three", value="Captain: ")
    bingo_info_embed.add_field(name="Team Four", value="Captain: ")
    bingo_info_embed.add_field(name="", value="")
    bingo_info_embed.add_field(name="Team Five", value="Captain: ")

    await ctx.send(embed=bingo_info_embed)


# "!bingome" command
# Displays custom bingo player profile card in an embed
# TODO: Track amount of posts in general channel as smack talk stat
# TODO: Integrate with WOM API
# TESTED GOOD
@bot.command()
async def me(ctx):
    global player_titles_dict

    # Getting member and if they're a captain
    team, isCaptain = await find_bingo_team(ctx.author)
    if team == None:
        await ctx.channel.send("You are not in the bingo.  But it's not too late to sign up!")
        return
    # Player custom title
    title = player_titles_dict.get(random.randint(1, len(player_titles_dict)))
    # Player custom smack_talk/quote
    smack_talk = get_smack_talk()

    # Custom settings for team captains
    if isCaptain:
        bingo_profile_embed = discord.Embed(
            title=f"Battle Bingo Player Stats",
            color=0xFFAB00,
            description="👑 Team Captain,"
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
    bingo_profile_embed.add_field(name="Team:", value=team)
    bingo_profile_embed.add_field(name="", value="")
    bingo_profile_embed.add_field(name="Submissions:", value="0")
    bingo_profile_embed.add_field(name="", value=smack_talk)

    await ctx.send(embed=bingo_profile_embed)


# "!bingosubmit" command
# Tile Submition Tool
# Takes attachments from message, sends to Google Doc for verification
# Data about the interaction is used for recognizing submissions
# TODO: IMPORTANT---Data persistance
@bot.command()
async def submit(ctx):

    # TODO: IMPORTANT---switch before going live
    # Targeting submissions in a specific channel
    # To prevent spam in rest of server
    if ctx.channel != bot.get_channel(BINGO_TEST_CHANNEL):
        return
    
    #task_id = message.content
    #print(task_id)
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if attachment.filename.endswith(
                (".png", ".jpg", "jpeg", "gif")
            ):
                id = str(uuid.uuid4())
                map_of_submissions[id] = ctx.message

                await post(ctx)

                # posting to google sheets
                # TODO: send team info, task id to sheets (gspread?)
                # TODO: from google, send back player success
                await post_bingo_submission(
                    attachment.url, id
                )

                # posting to #posthere channel
                await ctx.channel.send(
                    "I will take your submission to Bingo Overlord Foki for review."
                )

                # snarky options if desired
                # bot_response = random.randint(1, 10)
                # await message.channel.send(submission_responses_dict[bot_response])

                # posting logs to #logs channel
                await submission_alert(ctx, id)

            # Submission screenshot is the wrong file type
            else:
                await ctx.channel.send(
                    "The file type you have submitted is not supported.  Please use .png, .jpg, .jpeg, or .gif."
                )

    # No attachment on message
    else:
        await ctx.channel.send(
            "There was no attachment on that post. Your submission has been rejected."
        )


#
# HELPER FUNCTIONS
#

"""
Connects to Google API
CREDENTIALS_PATH - path to service account credentials .json file
SCOPES - scopes at Google required by the bot
returns Google Docs service object
"""


# done
async def connect_to_google():
    CREDENTIALS_PATH = "service_account.json"
    SCOPES = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=SCOPES
    )
    # Different build required per service (sheets, docs, etc.)
    service = build("docs", "v1", credentials=credentials)

    # LOG
    print(
        "{0.user.display_name}: Captain, we've started a communications link between us and Starfleet's Google API division.".format(
            bot
        )
    )

    return service


"""
Posts image to Google Doc
image_url - URL of image to be posted
id - UUID associated with submission
GOOGLE_DOCS_KEY - key to the specific Google Doc desired
Document is updated by sending HTTP requests to the Google service
Each request is a specific function (insertInlineImage, insertText, etc.)
With index 1, all requests appear at top of page (so should be posted in reverse order)
"""


async def post_bingo_submission(image_url, id):

    service = await connect_to_google()
    trimmedId = id[:8]

    # adding image to document via HTTP requests
    # creating each request
    insert_image = [{"insertInlineImage": {"location": {"index": 1}, "uri": image_url}}]
    insert_text = [
        {"insertText": {"location": {"index": 1}, "text": "{0}\n".format(id)}}
    ]
    insert_page_break = [{"insertPageBreak": {"location": {"index": 1}}}]

    # posting requests to Google
    update_1 = (
        service.documents()
        .batchUpdate(documentId=GOOGLE_DOCS_KEY, body={"requests": insert_page_break})
        .execute()
    )
    update_2 = (
        service.documents()
        .batchUpdate(documentId=GOOGLE_DOCS_KEY, body={"requests": insert_text})
        .execute()
    )
    update_3 = (
        service.documents()
        .batchUpdate(documentId=GOOGLE_DOCS_KEY, body={"requests": insert_image})
        .execute()
    )

    # LOG
    print(
        "{0.user}: Captain, we've received an incoming transmission.  Putting on screen.".format(
            client
        )
    )
    print("[] Received: Submission # {0}".format(trimmedId))


"""
Posts embed message to specific Discord channel with submission information
message - Discord message object
id - Submission UUID
BINGO_TEST_CHANNEL - Discord channel to post message to (channel ID)

"""


async def submission_alert(ctx, id):
    global map_of_embed_messages, map_of_embeds

    trimmedId = id[:8]
    d = datetime.datetime.now()
    # TODO: Switch to logs channel or w/e
    channel = bot.fetch_channel(BINGO_TEST_CHANNEL)
    # channel = ctx.channel

    # Creating the custom embed to track the submission
    submission_embed = discord.Embed(
        title=f"Submission #\n{trimmedId}", url=ctx.message.jump_url, color=0x0A0AAB
    )
    submission_embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
    submission_embed.set_thumbnail(url=ctx.message.attachments[0].url) # is .url needed here?
    submission_embed.add_field(name="Posted on: \n", value=d.strftime("%B %d %X"))
    
    # Posting embed the custom embed
    embed_message = await channel.send(embed=submission_embed)

    # saving new message and the custom embed for later operations
    map_of_embed_messages[id] = embed_message
    map_of_embeds[id] = submission_embed


"""
Approves submission by looking for a thumbs up message from the Google API
message - Discord message object
BINGO_TEST_CHANNEL - Discord channel to post message to (channel ID)
Splices the UUID out of the message, uses as key to retrieve specific embed and embed message.
Updates embed with approval time, deletes old post, creates new post.
"""

# done
async def approve(ctx):
    global map_of_submissions

    id = ctx.message.content.split()[5]
    trimmedId = id[:8]
    d = datetime.datetime.now()
    # TODO: IMPORTANT---change to production channel before launch
    channel = bot.fetch_channel(BINGO_TEST_CHANNEL)
    emoji = "✅"

    # bot adds reaction to submission post to show approval
    await map_of_submissions.get(id).add_reaction(emoji)

    # LOG
    print(
        "{0.user.display_name}: Captain, submission {1} has been approved.".format(bot, trimmedId)
    )

    embed = map_of_embeds.get(id)
    embed_message = map_of_embed_messages.get(id)
    embed.add_field(name="Approved on: /n", value=d.strftime("%B %d %X"))

    await embed_message.delete()
    await channel.send(embed=embed)


"""
Approves submission by looking for a thumbs up message from the Google API
message - Discord message object
TEST_LOGS_CHANNEL - Discord channel to post message to (channel ID)
Splices the UUID out of the message, uses as key to retrieve specific embed and embed message.
Updates embed with approval time, deletes old post, creates new post.
"""

# done
async def deny(ctx):    
    global map_of_submissions

    id = ctx.message.content.split()[5]
    trimmedId = id[:8]
    d = datetime.datetime.now()
    # TODO: change to 
    channel = bot.fetch_channel(BINGO_TEST_CHANNEL)
    emoji = "❌"

    # bot adds reaction to submission post to show approval
    await map_of_submissions.get(id).add_reaction(emoji)

    # LOG
    print(
        "{0.user.display_name}: Captain, submission {1} has been DENIED.".format(bot, trimmedId)
    )

    embed = map_of_embeds.get(id)
    embed_message = map_of_embed_messages.get(id)
    embed.add_field(name="DENIED on: /n", value=d.strftime("%B %d %X"))

    await embed_message.delete()
    await channel.send(embed=embed)


"""
Future testing function:
- TEST: handling many submissions very quickly
- TEST: handling submission with many attachments
"""


# done
async def test_submissions():
    pass


"""
Figure out what bingo team the command caller is on
message - Discord message object
BINGO_TEAM_ROLES - map of message id - bingo team names (string)
Cycle through all bingo teams, if user has role, return team name.
"""


# done
async def find_bingo_team(user):
    isCaptain = False
    roles = user.roles

    for i in roles:
        if i.id == CAPTAIN_ROLE:
            isCaptain = True

    for key in BINGO_TEAM_ROLES.keys():
        for role in roles:
            if key == role.id:
                # Returning team/captain?
                return (BINGO_TEAM_ROLES.get(key), isCaptain)

    return (None, None)

# done
"""
Gets smack talk from a dict of hardcoded entries, directed at random team.
Choose random team, pass team through hardcoded dict, return finalized string.
TODO: I do not like how this is coded.  Is there a better way?
"""
LIST_SIZE = 21

# done
def get_smack_talk():
    global BINGO_TEAM_ROLES

    team = "Test"
    while team == "Test":
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
        17: f"Maybe we should donate a few teammembers to {team} to help them out...",
        18: f"{team} who?",
        19: f"I bet {team} eats boneless wings.",
        20: f"{team} must play RS3.",
        21: f"Uh ... {team}'s gonna need more people.",
    }
    talk = random.randint(1, len(player_smack_talk))
    return player_smack_talk.get(talk)


"""
Creates a dropdown selector for each task
# TODO: automate task input instead of manual - use discord.Generator?
# TODO: button logic
Creates Discord component for selecting tasks, returns component
"""

# done
async def post(ctx):
    view = View()
    task_list_options = [
        discord.SelectOption(
            label="Task One", value=1, description="Kill a Chicken", default=False
        ),
        discord.SelectOption(
            label="Task Two", value=2, description="Salute a Goblin", default=False
        ),
        discord.SelectOption(
            label="Task Three", value=3, description="Eat an Anchovy", default=False
        ),
    ]
    task_submit_button = discord.ui.Button(
        label="Submit", custom_id="submit_task_button", style=discord.ButtonStyle.green
    )
    task_submit_menu = discord.ui.Select(
        options=task_list_options,
        custom_id="task_selection_component",
        placeholder="Select a Task",
        min_values=1,
        max_values=1,
    )
    view.add_item(task_submit_menu)
    view.add_item(task_submit_button)
    await ctx.send("Select which task you would like to complete below", view=view)

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

    # Custom discord announcement
    # await bot.get_channel(BINGO_GENERAL_CHANNEL).send("Fuck you back Sasa.")


"""
Static Discord bot event, triggers whenever a message is sent by a user.
"""


@bot.event
async def on_message(message):
    global num_submissions, map_of_submissions, client, player_titles_dict
    global EMBED_ICON_URL, RULES_POST_URL

    # Tells bot to ignore its own messages
    if message.author == bot.user:
        return

    # Finding out what team command caller is on
    team, isCaptain = await find_bingo_team(message.author)

    # Bot responds to commands sent from Google API via Webhook
    if message.content.startswith("✅"):
        await approve(message)
        return
    if message.content.startswith("❌"):
        await deny(message)
        return
    
    if team == "None":
        return

# DO NOTHING
"""

    ### "!bingorules" command
    # Points user in the direction of the rules post in Discord
    # TODO: FIX THIS METHOD
    if cmd == "rules":
        rules_channel = await client.fetch_channel(BINGO_GENERAL_CHANNEL)
        rules_message = await rules_channel.fetch_message(RULES_POST_MSG)
        print("have message")
        await message.channel.send(
            "You can find the rules for Battle Bingo here -> " + rules_message
        )

    ### "!bingorules" command
    elif cmd == "menu":
        bingo_info_embed = discord.Embed(
            title=f"Foki Bot Commands",
            color=0xFFBA00,
            description="Type these commands in any chat.",
        )
        bingo_info_embed.set_author(name=client.user, icon_url=client.user.avatar)
        bingo_info_embed.set_thumbnail(url=EMBED_ICON_URL)
        bingo_info_embed.add_field(name="!bingomenu", value="This menu.")
        bingo_info_embed.add_field(
            name="!bingoinfo", value="Information about the bingo event."
        )
        bingo_info_embed.add_field(name="!bingome", value="Your bingo player card.")
        bingo_info_embed.add_field(
            name="!bingorules", value="The official bingo rules."
        )
        bingo_info_embed.add_field(name="!bingowhen", value="Ping pong.")
        bingo_info_embed.add_field(
            name="!bingosubmit",
            value="UNDER CONSTRUCTION DO NOT USE\nTile Submission Tool, used to submit your tile completion screenshots.",
        )

        await message.channel.send(embed=bingo_info_embed)

    ### CHANNEL COMMANDS
    # Targeting #bingo-general
    # if message.channel == client.get_channel(BINGO_GENERAL_CHANNEL):

    # Targeting messages in Test server

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

        # quick response action
        elif message.content.startswith("!ping"):
            await message.channel.send("pong")
            return
"""

# Runs the bot
bot.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)


# FUTURE IDEAS

# - show board command
# - show teams command
# - show current board state?

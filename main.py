import discord
import discord.ext.commands
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

### CONSTANTS
# AUTH
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_DOCS_KEY = os.getenv("GOOGLE_DOCS_KEY")
# TEST CHANNELS & WEBHOOKS
TEST_SUBMISSIONS_CHANNEL = 1194832130962890842
TEST_LOGS_CHANNEL = 1194488938480537740
TEST_WEBHOOK_USER_ID = 1194889597738549298
# LIVE CHANNELS & WEBHOOKS
BINGO_GENERAL_CHANNEL = 1193039460980502578
# BINGO_SUBMISSIONS_CHANNEL = 
# BINGO_WEBHOOK_USER_ID = 
# DISCORD TEAM ROLES (IDS: NAMES)
BINGO_ROLES = {
    1195523300277895189: "Team One",
    1195523386621825177: "Team Two",
    1195523436685049897: "Team Three",
    1195523498299371570: "Team Four",
    1195523607384834060: "Team Five",
    # For testing
    1195556259160666172: "Test"
}
# URLs & MESSAGES
EMBED_ICON_URL = "https://shorturl.at/wGOXY"
RULES_POST_URL = "https://discord.com/channels/741153043776667658/1193039460980502578/1193042254751879218"
RULES_POST_MSG = 1193042254751879218

### VARIABLES
# MAPS
map_of_submissions = {}
map_of_embeds = {}
map_of_embed_messages = {}
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
    6: "Spooned",
    7: "Crafty",
    8: "Humble",
    9: "Terrible"
}

# Custom smack talk, can throw anywhere
player_smack_talk = {
    1: "Team Four doesn't stand a chance!",
    2: "Are you sure Team Two is playing the right bingo?  It seems like they took a wrong turn on the way to mediocrity.",
    3: "Team One's strategy is so outdated; it's like playing chess against a team of checkers enthusiasts.",
    4: "I'm not sure what Team Three's problem is, but I'd be willing to be that it's something hard to pronounce.",
    5: "Brain's aren't everything.  And in Team Five's case, they're nothing."
}

# MISC
num_submissions = 0

# DISCORD AUTH
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
# TEST
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")


### FUNCTIONS

"""
Connects to Google API
CREDENTIALS_PATH - path to service account credentials .json file
SCOPES - scopes at Google required by the bot
returns Google Docs service object
"""


async def connect_to_google():
    global client

    CREDENTIALS_PATH = "service_account.json"
    SCOPES = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=SCOPES
    )
    # different build per service (sheets, docs, etc.)
    service = build("docs", "v1", credentials=credentials)

    # LOG
    print(
        "{0.user}: Captain, we've started a communications link between us and Starfleets Google API division.".format(
            client
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


async def post_image(image_url, id):
    global client

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
TEST_LOGS_CHANNEL - Discord channel to post message to (channel ID)

"""


async def submission_alert(message, id):
    global map_of_embed_messages, map_of_embeds

    trimmedId = id[:8]
    d = datetime.datetime.now()
    channel = client.get_channel(TEST_LOGS_CHANNEL)

    # creating the custom embed
    embed = discord.Embed(
        title=f"Submission #\n{trimmedId}", url=message.jump_url, color=0x0A0AAB
    )
    embed.set_author(name=message.author, icon_url=message.author.avatar)
    embed.set_thumbnail(url=message.attachments[0].url)
    embed.add_field(name="Posted on: \n", value=d.strftime("%B %d %X"))
    # posting embed
    embed_message = await channel.send(embed=embed)

    # saving new message and the custom embed for later operations
    map_of_embed_messages[id] = embed_message
    map_of_embeds[id] = embed


"""
Approves submission by looking for a thumbs up message from the Google API
message - Discord message object
TEST_LOGS_CHANNEL - Discord channel to post message to (channel ID)
Splices the UUID out of the message, uses as key to retrieve specific embed and embed message.
Updates embed with approval time, deletes old post, creates new post.
"""


async def approve(message):
    global map_of_submissions

    id = message.content.split()[5]
    trimmedId = id[:8]
    d = datetime.datetime.now()
    channel = client.get_channel(TEST_LOGS_CHANNEL)
    emoji = "✅"

    # bot adds reaction to submission post to show approval
    await map_of_submissions.get(id).add_reaction(emoji)

    # LOG
    print(
        "{0.user}: Captain, submission {1} has been approved.".format(client, trimmedId)
    )

    embed = map_of_embeds.get(id)
    embed_message = map_of_embed_messages.get(id)
    embed.add_field(name="Approved on: /n", value=d.strftime("%B %d %X"))

    await embed_message.delete()
    await channel.send(embed=embed)


"""
Future testing function, pass a bunch of submissions at once
"""


async def test_submissions():
    pass

"""
Figure out what bingo team the command caller is on
message - Discord message object
BINGO_ROLES - map of message id - bingo team names (string)
Cycle through all bingo teams, if user has role, return team name.
"""

#@bot.command()
# TODO: isCaptain
async def find_bingo_team(message):
    roles = message.author.roles

    for key in BINGO_ROLES.keys():
        for role in roles:
            if key == role.id:
                return BINGO_ROLES.get(key)
    return "None"


### DISCORD BOT CODE

"""
Static Discord bot event, triggers whenever bot finishes booting up.
"""


@client.event
async def on_ready():
    # LOG
    print("{0.user}: Captain, the warp core is ready to go.".format(client))


"""
Static Discord bot event, triggers whenever a message is sent by a user.
"""


# TODO: refactor code so quicker exit commands are on top
# TODO: match team color to profile embed, or random colors
# TODO: SAVE THE DATA!! reboot from save command?  save data manually command?
# TODO: commands list
# TODO: swap to bot.commands
# TODO: add toggleable options
# TODO: 
@client.event
async def on_message(message):
    global num_submissions, map_of_submissions, client, player_titles_dict
    global EMBED_ICON_URL, RULES_POST_URL

    # Tells bot to ignore its own messages
    if message.author == client.user:
        return

    # Finding out what team command caller is on
    team = await find_bingo_team(message)

    # Bot responds to messages from the Google API
    if message.content.startswith("Google"):
        await approve(message)
        return

    # Bot command trigger
    if message.content.startswith("!bingo"):

        # If command caller isn't in the bingo
        if team == "None":
            await message.channel.send("You are not in the bingo.  But it's not too late to sign up!")
            return
        
        # Slicing command from message string
        cmd = message.content[6:]
        # LOG
        process_message = await message.channel.send("Processing...")

        ### GLOBAL COMMANDS

        ### "!bingoinfo" command
        # Displays information about the bingo event
        if cmd == "info":
            # Link to bingo information post on Discord

            bingo_info_embed = discord.Embed(
                title=f"Battle Bingo Information", url=RULES_POST_URL, color=0xFF0000
            )
            bingo_info_embed.set_author(name=client.user, icon_url=client.user.avatar)
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

            await message.channel.send(embed=bingo_info_embed)

        ### "!bingome" command
        # Displays custom bingo player profile card in an embed
        # TODO: Custom embed for Captains? run through Foki
        elif cmd == "me":
            title = player_titles_dict.get(random.randint(1,10))
            insult = player_smack_talk.get(random.randint(1,5))
            
            bingo_profile_embed = discord.Embed(
                title=f"Battle Bingo Player Stats", color=0x0000FF
            )
            bingo_profile_embed.set_author(
                name=f"{message.author.display_name} the {title}", icon_url=message.author.avatar
            )
            bingo_profile_embed.set_thumbnail(url=EMBED_ICON_URL)
            bingo_profile_embed.add_field(name="Team:", value=team)
            bingo_profile_embed.add_field(name="", value="")
            bingo_profile_embed.add_field(name="Submissions:", value="0")
            bingo_profile_embed.add_field(name="", value=insult)

            await message.channel.send(embed=bingo_profile_embed)
            await process_message.delete()
            return

        ### "!bingorules" command
        # Points user in the direction of the rules post in Discord
        elif cmd == "rules":
            rules_channel = await client.fetch_channel(BINGO_GENERAL_CHANNEL)
            rules_message = await rules_channel.fetch_message(RULES_POST_MSG)
            print("have message")
            await message.channel.send(
                "You can find the rules for Battle Bingo here -> "
                + rules_message
            )

        ### CHANNEL COMMANDS
        # Targeting #bingo-general*
        if message.channel == client.get_channel(BINGO_GENERAL_CHANNEL):
            ### "!bingowhen" command
            # Ping pong
            if cmd == "when":
                await message.channel.send("👀")

        # Targetting #bingo-submissions
        """
        if message.channel == client.get_channel(BINGO_SUBMISSIONS_CHANNEL):
            ### "!bingosubmit" command
            # For handling bingo submissions
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
                            await post_image(attachment.url, id)

                            # posting to #posthere channel
                            await message.channel.send(
                                "Your submission has been successfully submitted to the Bingo council."
                            )

                            # snarky options if desired
                            # bot_response = random.randint(1, 10)
                            # await message.channel.send(submission_responses_dict[bot_response])

                            # posting logs to #logs channel
                            await submission_alert(message, id)

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
                            await post_image(attachment.url, id)

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

        # Deleting processing message
        await process_message.delete()


# Runs the bot
client.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)


# FUTURE IDEAS

# - show board command
# - show teams command
# - show current board state?
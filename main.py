import discord
import logging
import datetime
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
import uuid

### variables and constants
num_submissions = 0
load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_DOCS_KEY = os.getenv("GOOGLE_DOCS_KEY")
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

TEST_SUBMISSIONS_CHANNEL = 1194832130962890842
TEST_LOGS_CHANNEL = 1194488938480537740
TEST_WEBHOOK_USER_ID = 1194889597738549298

BINGO_GENERAL_CHANNEL = 1193039460980502578

map_of_submissions = {}
map_of_embeds = {}
map_of_embed_messages = {}

foki_responses_dict = {
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


### helper functions


# function to connect to google docs
# returns 'Bingo Test' google docs document
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
    service = build("docs", "v1", credentials=credentials)

    print(
        "{0.user}: Captain, we've started a communications link between us and Starfleets Google API division.".format(
            client
        )
    )

    # location = service.documents().get(documentId=GOOGLE_DOCS_KEY).body.content.endIndex
    # print(location)

    return service


# function to post image to doc
async def post_image(image_url, id):
    global client
    service = await connect_to_google()

    # adding image to document
    insert_image = [{"insertInlineImage": {"location": {"index": 1}, "uri": image_url}}]
    insert_text = [
        {"insertText": {"location": {"index": 1}, "text": "{0}\n".format(id)}}
    ]
    insert_page_break = [{"insertPageBreak": {"location": {"index": 1}}}]

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
    # insert_inline_image_response = response.get("replies")[0].get("insertInlineImage")

    # logging submission
    print(
        "{0.user}: Captain, we've received an incoming transmission.  Putting on screen.".format(
            client
        )
    )
    trimmedId = id[:8]
    print("[] Received: Submission # {0}".format(trimmedId))


# posts custom embed to logs channel
async def submission_alert(message, id):
    global num_submissions, map_of_embed_messages, map_of_embeds
    trimmedId = id[:8]
    d = datetime.datetime.now()
    channel = client.get_channel(TEST_LOGS_CHANNEL)
    embed = discord.Embed(
        title=f"Submission #\n{trimmedId}", url=message.jump_url, color=0x0A0AAB
    )
    embed.set_author(name=message.author, icon_url=message.author.avatar)
    embed.set_thumbnail(url=message.attachments[0].url)
    embed.add_field(name="Posted on: /n", value=d.strftime("%B %d %X"))

    embed_message = await channel.send(embed=embed)
    map_of_embed_messages[id] = embed_message
    map_of_embeds[id] = embed


# approve
async def approve(message):
    global map_of_submissions
    id = message.content.split()[5]
    trimmedId = id[:8]

    d = datetime.datetime.now()
    channel = client.get_channel(TEST_LOGS_CHANNEL)
    emoji = "✅"

    await map_of_submissions.get(id).add_reaction(emoji)
    print(
        "{0.user}: Captain, submission {1} has been approved.".format(client, trimmedId)
    )

    embed = map_of_embeds.get(id)
    embed_message = map_of_embed_messages.get(id)
    embed.add_field(name="Approved on: /n", value=d.strftime("%B %d %X"))

    await embed_message.delete()
    await channel.send(embed=embed)
    return


### discord code


@client.event
# login event, triggers once bot is ready and working
async def on_ready():
    # log
    print("{0.user}: Captain, the warp core is ready to go.".format(client))


@client.event
# message event, triggers when a message is sent
async def on_message(message):
    global num_submissions, map_of_submissions

    # ignores own messages
    if message.author == "client.user":
        return

    # responses from the google api
    if message.content.startswith("Google"):
        await approve(message)
        return

    # targeting messages from Sith #bingo-general
    if message.channel == client.get_channel(BINGO_GENERAL_CHANNEL):
        if message.content.startswith("!bingo"):
            cmd = message.content[6:]

            ### bingowhen  command
            if cmd == "when":
                await message.channel.send("👀")

    # targeting the test submissions channel
    if message.channel == client.get_channel(TEST_SUBMISSIONS_CHANNEL):
        if message.content.startswith("!bingo"):
            cmd = message.content[6:]
            await message.channel.send("Processing...")

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
                            await submission_alert(message, id)
                            return

                        # wrong file type
                        else:
                            await message.channel.send(
                                "The file type you have submitted is not supported.  Please use .png, .jpg, .jpeg, or .gif."
                            )
                            return

                # no attachment on message
                else:
                    await message.channel.send(
                        "There was no attachment on that post. Your submission has been rejected."
                    )
                    return

        # quick response action
        elif message.content.startswith("!ping"):
            await message.channel.send("pong")
            return


# runs the bot
client.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)


# IDEAS

# - rules command
# - tiles/map command
# - teams command
# - completed tiles command

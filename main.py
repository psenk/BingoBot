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
SUBMISSIONS_CHANNEL = 1194832130962890842
LOGS_CHANNEL = 1194488938480537740
WEBHOOK_USER_ID = 1194889597738549298


map_of_submissions = {}
map_of_embeds = {}
map_of_embed_messages = {}


# submission responses
submission_responses_dict = {
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

    #print("{0.user}: Connected to Google API.".format(client))

    # location = service.documents().get(documentId=GOOGLE_DOCS_KEY).body.content.endIndex
    # print(location)

    return service

# function to post image to doc
async def post_image(image_url, id):
    global client
    service = await connect_to_google()

    # adding image to document
    request_one = [{"insertInlineImage": {"location": {"index": 1}, "uri": image_url}}]
    request_two = [{"insertText": {"location": {"index": 1}, "text": "{0}\n".format(id)}}]
    request_three=[{"insertPageBreak": {"location": {"index": 1}}}]
    
    response_one = (
        service.documents().batchUpdate(documentId=GOOGLE_DOCS_KEY, body={"requests": request_three}).execute()
    )    
    response_two = (
        service.documents().batchUpdate(documentId=GOOGLE_DOCS_KEY, body={"requests": request_one}).execute()
    )
    response_three = (
        service.documents().batchUpdate(documentId=GOOGLE_DOCS_KEY, body={"requests": request_two}).execute()
    )
    # insert_inline_image_response = response.get("replies")[0].get("insertInlineImage")

    # logging submission
    print(
        "{0.user}: Captain, we've received an incoming transmission.  Putting on screen.".format(
            client
        )
    )
    print("[] Received: Submission # {0}".format(id))

# posts custom embed to logs channel
async def submission_alert(message, id):
    global num_submissions, map_of_embed_messages, map_of_embeds
    d = datetime.datetime.now()
    channel = client.get_channel(LOGS_CHANNEL)
    embed = discord.Embed(
        title=f"Submission #\n{id}", url=message.jump_url, color=0x0A0AAB
    )
    embed.set_author(name=message.author, icon_url=message.author.avatar)
    embed.set_thumbnail(url=message.attachments[0].url)
    embed.add_field(name="Posted on: ", value=d.strftime("%B %d %X"))
    
    await channel.send(embed=embed)
    map_of_embed_messages[num_submissions] = message
    map_of_embeds[num_submissions] = embed

    
async def approve(message):
    global map_of_submissions
    id = message.content.split()[5]
    
    d = datetime.datetime.now()
    channel = client.get_channel(LOGS_CHANNEL)    
    emoji = '✅'   
    
    print("Message ID: {0}".format(id))
    print(map_of_submissions.keys)
    print("Message: {0}".format(map_of_submissions.get(id)))
    
    await map_of_submissions.get(id).add_reaction(emoji)
    print("{0.user}: Captain, a submission has been approved.".format(client))
        
    embed = map_of_embeds.get(id)
    embed_message = map_of_embed_messages.get(id)
    embed.add_field(name="Approved on: ", value=d.strftime("%B %d %X"))
    
    await embed_message.delete()
    await channel.send(embed=embed)
    return

### discord code


# login event, triggers once bot is ready and working
@client.event
async def on_ready():
    # log
    print("{0.user}: Captain, the warp core is ready to go.".format(client))


# message event, triggers when a message is sent
@client.event
async def on_message(message):
    global num_submissions, map_of_submissions
    if message.author == "client.user":
        return
    
    if message.content.startswith("Google"):
        await approve(message)
        
    # targeting a specific channel
    if message.channel == client.get_channel(SUBMISSIONS_CHANNEL):
        ### bingosubmit command
        if message.content.startswith("!bingosubmit"):
            await message.channel.send("`Processing...`")
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.filename.endswith((".png", ".jpg", "jpeg", "gif")):
                        num_submissions += 1
                        id = uuid.uuid4();
                        map_of_submissions[id] = message
                        
                        # posting to google sheets
                        await post_image(attachment.url, id)

                        # posting to #posthere channel
                        await message.channel.send(
                            "`Your submission has been successfully submitted to the Bingo council.`"
                        )
                        
                        # snarky options if desired
                        #bot_response = random.randint(1, 10)
                        #await message.channel.send(submission_responses_dict[bot_response])

                        # posting logs to #logs channel
                        await submission_alert(message, id)
                        return
                    
                    # wrong file type
                    else:
                        await message.channel.send("`The file type you have submitted is not supported.  Please use .png, .jpg, .jpeg, or .gif.`")
                        return

            # no attachment on message
            else:
                await message.channel.send("`There was no attachment on that post. Your submission has been rejected.`")
                return
        elif message.content.startswith("!ping"):
            await message.channel.send("pong")
            return
# runs the bot
client.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)

# IDEAS
# - submit command
# - - send to google sheets?
# - rules command
# - tiles/map command
# - teams command
# - completed tiles command

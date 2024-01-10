import discord
from discord.ext import commands
import gspread
import os
import logging
import random
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO
import time
import datetime

# variables and constants
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
handler = logging.FileHandler(filename='discord.log',
                              encoding='utf-8',
                              mode='w')
SUBMISSIONS_CHANNEL = 1194488938480537740
num_submissions = 0

# submission responses
submission_responses_dict = {
    1: 'DID YOU REMEMBER YOUR CODEWORD?',
    2: 'REALLY? THIS IS YOUR SUBMISSION? ARE YOU SURE?',
    3: 'YOU\'RE THE FIRST PERSON TO SUBMIT THIS! PROBABLY. MAYBE.',
    4: 'ABOUT TIME.',
    5: 'FINALLY!',
    6: 'ARE YOU WAITING FOR A TIP? GO AWAY.',
    7: 'CONGRATS {USER} FOR YOUR DROP/ACHIEVEMENT/THING!',
    8: 'FOKI ALREADY HAS ONE OF THESE, SO...',
    9: 'TOOK YA LONG ENOUGH!',
    10: 'FUCK YOU DJ'
}


# login event, triggers once bot is ready and working
@client.event
async def on_ready():
  print('{0.user} ONLINE'.format(client))


# message event, triggers when a message is sent
@client.event
async def on_message(message):
  global num_submissions
  if message.author == client.user:
    return

  if message.content.startswith('!bingosubmit'):
    if message.attachments:
      for attachment in message.attachments:
        if attachment.filename.endswith(('.png', '.jpg', 'jpeg', 'gif')):
          image_url = attachment.url
          await post_image(message, image_url)
          await message.channel.send('SUBMISSION RECEIVED')
          num_submissions += 1
          await submission_alert(message)
    
    else:
      await message.channel.send('NO FILE ATTACHED. SUBMISSION REJECTED.')
      return

    bot_response = random.randint(1, 10)
    await message.channel.send(submission_responses_dict[bot_response])


# function to post image to google sheets
async def post_image(message, image_url):
  pass

async def submission_alert(message):
  d = datetime.datetime.now()
  channel = client.get_channel(SUBMISSIONS_CHANNEL)
  await message.channel.send('message')

# run the bot
client.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)

# IDEAS
# - submit command
# - - send to google sheets?
# - rules command
# - tiles/map command
# - teams command
# - completed tiles command

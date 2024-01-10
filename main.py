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
GOOGLE_SHEETS_ID = os.environ['GOOGLE_SHEETS_KEY']
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

          # posting to google sheets
          await post_image(message, image_url)

          # posting to submission channel
          await message.channel.send('SUBMISSION RECEIVED')
          num_submissions += 1

          # posting for logs/status
          await submission_alert(message)

    # no attachment on message
    else:
      await message.channel.send('NO FILE ATTACHED. SUBMISSION REJECTED.')
      return

    bot_response = random.randint(1, 10)
    await message.channel.send(submission_responses_dict[bot_response])


# function to post image to google sheets
async def post_image(message, image_url):

  CREDENTIALS_PATH = '/google_creds.json'
  SCOPE = 'https://www.googleapis.com/auth/spreadsheets'
  SHEET_NAME = 'Bingo Approval Form'
  # print('in post_image method')

  # connect to google sheets
  credentials = ServiceAccountCredentials.from_json_keyfile_name(
      CREDENTIALS_PATH, SCOPE)
  gc = gspread.authorize(credentials)
  sheet = gc.open_by_key(GOOGLE_SHEETS_ID).sheet1
  print('connected to google sheets')

  # post image
  #next_row = len(sheet.get_all_values()) + 1
  #sheet.update_cell(next_row, 1, image_url)
  #sheet.update_cell(next_row, 2, message.author)


async def submission_alert(message):
  d = datetime.datetime.now()
  channel = client.get_channel(SUBMISSIONS_CHANNEL)
  embed = discord.Embed(title=f'Submission #{num_submissions}',
                        url=message.jump_url,
                        color=0x0a0aab)
  embed.set_author(name=message.author, icon_url=message.author.avatar)
  embed.set_thumbnail(url=message.attachments[0].url)
  embed.add_field(name='Posted on: ', value=d.strftime('%B %d %X'))
  await channel.send(embed=embed)


# run the bot
client.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)

# IDEAS
# - submit command
# - - send to google sheets?
# - rules command
# - tiles/map command
# - teams command
# - completed tiles command

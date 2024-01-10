import discord
import os
import logging

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# login event, triggers when bot is ready and working
@client.event
async def on_ready():
  print('{0.user} ONLINE'.format(client))


# message event, triggers when a message is sent
@client.event
async def on_message(message):
  if message.author == client.user:
    return

  if message.content.startswith('!bingo'):
    await message.channel.send('TRANSMISSION RECEIVED')


# run the bot
client.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)

# this example requires the 'message_content' intent.

import discord
import os
import llm

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message: discord.message.Message):
    if message.author == client.user:
        return

    if message.content.lower().startswith('ai'):
        async with message.channel.typing():
            reply = llm.reply(message.content)

        await message.channel.send(reply)


client.run(os.environ['DISCORD_BOT_TOKEN'])
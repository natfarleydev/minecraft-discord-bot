# this example requires the 'message_content' intent.

import discord
import os
import llm
from memory import add_to_memory

intents = discord.Intents.default()
intents.message_content = True


class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
    
    async def on_message(self, message: discord.message.Message):
        add_to_memory(message.channel.id, message)
        if message.author == client.user:
            return

        if message.content.lower().startswith('ai') or message.channel.type == discord.ChannelType.private:
            async with message.channel.typing():
                reply = await llm.reply(message.content, message.channel.id)
                # await message.channel.send(f'{reply["response"]}\n\n[Input tokens: {reply["input_token_count"]}, Output tokens: {reply["output_token_count"]}, Cost: ${reply["cost"]}]')
                await message.channel.send(f'{reply["response"]}')
        
    
    async def on_error(self, event_method: str, /, *args, **kwargs):
        # TODO make LLM format this error message
        await args[0].channel.send(f'Error, {event_method}, {args}, {kwargs}')
        await super().on_error(event_method, *args, **kwargs)

client = MyClient(intents=intents)

client.run(os.environ['DISCORD_BOT_TOKEN'])
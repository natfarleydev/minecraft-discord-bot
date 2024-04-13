# this example requires the 'message_content' intent.

import discord
import os
import llm
from memory import add_to_memory
import traceback
import sys

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
                print("Sending message:")
                from pprint import pprint
                pprint(reply)
                await message.channel.send(f'{reply["response"]}\n\n--- Input tokens: {reply["input_token_count"]}, Output tokens: {reply["output_token_count"]}, Cost: ${reply["cost"]} ---')
                # await message.channel.send(f'{reply["response"]}')
        
    
    async def on_error(self, event_method: str, /, *args, **kwargs):
        # TODO make LLM format this error message
        await args[0].channel.send(f'Something went wrong, let me check it out :thumbsup:')
        try:
            async with args[0].channel.typing():
                exception_type, exception, tb = sys.exc_info()
                traceback_list = traceback.format_tb(tb)
                formatted_traceback = "".join(traceback_list)

                exception_information_for_prompt = f'Exception type: `{exception_type}`\n\nException: `{exception}`\n\nTraceback:\n```\n{formatted_traceback}\n```'
                
                # Here we use the raw LLM because if we try and use tools, the tools freak out and don't understand what to do with exception information.
                reply = await llm.chain.ainvoke(
                    {"input": f'Your task is to explain this error to the user and suggest remedial action. Do not offer to help or imply in any way that you can do anything about the error (you are a bot an incapable of changing your own programming). Reply in friendly but terse language, without backticks. Information about the error is below. \n\n{exception_information_for_prompt}'},
                )
                response = reply + '\n\n---\n\n' + exception_information_for_prompt
                await args[0].channel.send(response)
        except Exception as e:
            await args[0].channel.send(f'Oh no! I couldn\'t figure out what went wrong. (For the developer, the bot tried to reply but hit the following error {e})')
            traceback.print_exc()
        await super().on_error(event_method, *args, **kwargs)

client = MyClient(intents=intents)

client.run(os.environ['DISCORD_BOT_TOKEN'])
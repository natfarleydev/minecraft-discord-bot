from collections import defaultdict
import discord

memory: dict[int, list[discord.message.Message]] = defaultdict(list)

MEMORY_LIMIT = 10

def add_to_memory(channel_id: int ,msg: discord.message.Message):
    memory[channel_id].append(msg)
    if len(memory) > MEMORY_LIMIT:
        memory.pop(0)

def get_memory():
    return memory

def format_memory_for_llm(channel_id: int):
    return "\n".join([f"{'AI' if 'PickaxePartner' in m.author.display_name else m.author.name}: {m.content}" for m in memory[channel_id]])
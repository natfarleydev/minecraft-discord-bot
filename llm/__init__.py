from typing import TypedDict

from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages.ai import AIMessage
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_anthropic.output_parsers import ToolsOutputParser

from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor



from memory import format_memory_for_llm

from .tools import search, turn_minecraft_server_on_or_off



token_counting_llm = ChatAnthropic(
    model_name="claude-3-haiku-20240307",
)

llm = ChatAnthropic(
    model_name="claude-3-haiku-20240307",
    temperature=0.2,
    # Discord has a max of 2000 words so we attempt to keep the token count down to below that.
    max_tokens_to_sample=400,
)


tools_llm = ChatAnthropic(
    model_name="claude-3-haiku-20240307",
)

tools = [search, turn_minecraft_server_on_or_off]
tools_llm = tools_llm.bind_tools(tools)
# tools_parser = ToolsOutputParser(=tools)
# tools_chain = with_tools | tools_parser


prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a helpful, friendly assistant. You aid with requests from discord related to a minecraft server, and Minecraft Java Edition in general.

Your tone is conversational and super chill, incorporating emoji's where possible. Keep messages short and to the point. Unless giving a direct answer to a question, limit answers to a single line. The exception is instructions, when you are giving instructions be as detailed as you can be.

If you have recieved URLS, use them as references in your response.

Format your response as a message in discord. Do not add comments.
     
     """),
     ("user", "{input}"),
])

# agent = create_tool_calling_agent(llm, tools, prompt)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

output_parser = StrOutputParser()

chain = prompt | llm | output_parser

class RetvalType(TypedDict):
    response: str
    input_token_count: int
    output_token_count: int
    cost: float | None
async def reply(prompt, channel_id: int) -> RetvalType:
    tools_response: AIMessage = await tools_llm.ainvoke(prompt)
    tools_to_call = tools_response.tool_calls

    prompt = ""
    if tools_to_call:
        prompt += "Tools output:"

    for tool_call in tools_to_call:
        match tool_call["name"]:
            case "search":
                prompt += "\n\nSearch output:"
                prompt += await search.arun(tool_call["args"])
            case "turn_minecraft_server_on_or_off":
                prompt += "\n\nMinecraft server on/off output:"
                prompt += await turn_minecraft_server_on_or_off.arun(tool_call["args"])

    prompt += f"\n\nPrevious messages: {format_memory_for_llm(channel_id)}\n\nUser message: {prompt}"
    response = await chain.ainvoke({"input": prompt})

    retval: RetvalType = {
        "response": response,
        "input_token_count": token_counting_llm.get_num_tokens(prompt),
        "output_token_count": token_counting_llm.get_num_tokens(response),
        "cost": None,
    }
    retval["cost"] = 0.25 * retval["input_token_count"]/1_000_000.0 + 1.25 * retval["output_token_count"]/1_000_000
    return retval
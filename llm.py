from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate

# TODO replace with haiku and low temperature
llm = ChatAnthropic(model_name="claude-3-haiku-20240307", temperature=1)

prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a helpful, friendly assistant. You aid with requests related to a minecraft server, and Minecraft Java Edition in general.

Your tone is conversational and super chill, incorporating emoji's where possible. Keep messages short and to the point. Unless giving a direct answer to a question, limit answers to a single line. The exception is instructions, when you are giving instructions be as detailed as you can be.
     
     """),
    ("user", "{input}")
])

output_parser = StrOutputParser()

chain = prompt | llm | output_parser

def reply(prompt):
    return chain.invoke({"input": prompt})
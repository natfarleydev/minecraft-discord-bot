from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun

# TODO replace with haiku and low temperature
llm = ChatAnthropic(model_name="claude-3-haiku-20240307", temperature=0.1)

prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a helpful, friendly assistant. You aid with requests from discord related to a minecraft server, and Minecraft Java Edition in general.

Your tone is conversational and super chill, incorporating emoji's where possible. Keep messages short and to the point. Unless giving a direct answer to a question, limit answers to a single line. The exception is instructions, when you are giving instructions be as detailed as you can be.
     
     """),
    ("user", "{input}")
])

output_parser = StrOutputParser()

chain = prompt | llm | output_parser

search_term_chain = ChatPromptTemplate.from_messages([
    ("system", "You will recieve a message from discord. Your task is to generate a single search phrase that will aid in helping that query. You reply only with the search term. You are forbidden from using punctuation of any kind."),
    ("user", "{input}")
]) | llm | output_parser

def reply(prompt):
    search = DuckDuckGoSearchRun()
    search_term = search_term_chain.invoke({"input": prompt}) + ", Minecraft Java edition"
    print(f"Search term: {search_term}")
    search_result = search.run(search_term)
    return chain.invoke({"input": "Discord message: " + prompt + f"\n\n The following is some supporting information from the web: {search_result}"})
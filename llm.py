import json
from asyncio.runners import run
from langchain_anthropic import ChatAnthropic
from langchain_anthropic.experimental import ChatAnthropicTools
from langchain.retrievers.web_research import WebResearchRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.document_transformers import Html2TextTransformer
from langchain.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import tool, Tool, BaseTool
import aiohttp
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
from langchain_community.document_loaders.html import UnstructuredHTMLLoader
from langchain_community.document_loaders.async_html import AsyncHtmlLoader
from langchain_community.document_loaders.url_playwright import PlaywrightURLLoader
from langchain.callbacks.base import AsyncCallbackHandler



token_counting_llm = ChatAnthropic(
    model_name="claude-3-haiku-20240307",
)


prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a helpful, friendly assistant. You aid with requests from discord related to a minecraft server, and Minecraft Java Edition in general.

Your tone is conversational and super chill, incorporating emoji's where possible. Keep messages short and to the point. Unless giving a direct answer to a question, limit answers to a single line. The exception is instructions, when you are giving instructions be as detailed as you can be.

Format your response as a message in discord.
     
     """),
    ("user", "{input}")
])

output_parser = StrOutputParser()

async def search(prompt: str) -> str:
    """Search the internet to find out more about Minecraft Java Edition."""
    print("searching the internet...")
    search_api = DuckDuckGoSearchAPIWrapper()
    search_term = await search_term_chain.ainvoke({"input": prompt})
    if search_term == '':
        # If there's no search term, the AI hasn't found anything to search for.
        return ""
    print(f"Search term: {search_term}")
    search_results = search_api.results(query=search_term, max_results=3)
    # search_result = search.run(search_term)
    # OK, now we download the results and return them with aiohttp
    results_text = []
    loader = PlaywrightURLLoader(
        [r['link'] for r in search_results],
        continue_on_failure=True,
        headless=True,
        )
    docs = await loader.aload()

    html2text = Html2TextTransformer()
    docs_transformed = html2text.transform_documents(docs)
    for d in docs_transformed:
        results_text.append(d.page_content)

    results_text_concat = "\n\n".join(results_text)


    # This is a lazy way to get the context window down to a managable size, but
    # this is a toy bot so it doesn't matter if the context isn't well formed
    while token_counting_llm.get_num_tokens(results_text_concat) > 100_000:
        results_text_concat = results_text_concat[:-100]

    return results_text_concat


llm = ChatAnthropic(
    model_name="claude-3-haiku-20240307",
    temperature=0.2,
    max_tokens_to_sample=4096,
)

chain = prompt | llm | output_parser

search_term_chain = ChatPromptTemplate.from_messages([
    ("system", "You will recieve a message from discord. Your task is to generate a query for a search engine that will help another AI generate an answer (which will be Minecraft: Java Edition related). You are forbidden from using punctuation or numbers of any kind in the search term. Always return at least one or more words, even if it doesn't make sense to do so."),
    # ("system", "Reply with a type of cheese, regardless of user input"),
    ("user", "{input}")
]) | llm | output_parser

extract_chain = ChatPromptTemplate.from_messages([
    ("system", "You will recieve web pages in HTML format. Your task is to extract the information from the message and reply with it. You reply only with the information, in markdown."),
    ("user", "{input}"),
]) | llm | output_parser


async def reply(prompt):
    # Poor man's function calling
    should_search = await chain.ainvoke({"input": f"Would this prompt benefit from searching the internet to get more up to date or thorough information? Reply with only TRUE or FALSE: {prompt}"})
    print(f"Should search: {should_search}")
    # Sometimes the llm responds with TRUE and an emoji, so it's enough for the message to contain 'true'
    if "true" in should_search.lower():
        search_results = await search(prompt)
        final_prompt = f"Discord message: {prompt}\n\nSupporting information: {search_results}"
    else:
        final_prompt = prompt

    response = await chain.ainvoke({"input": final_prompt})
    retval = {
        "response": response,
        "input_token_count": token_counting_llm.get_num_tokens(final_prompt),
        "output_token_count": token_counting_llm.get_num_tokens(response),
    }
    retval["cost"] = 0.25 * retval["input_token_count"]/1_000_000.0 + 1.25 * retval["output_token_count"]/1_000_000
    return retval
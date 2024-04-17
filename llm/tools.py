import asyncio
from typing import Type
from langchain.pydantic_v1.main import BaseModel

from typing import Tuple
from langchain.tools import tool, BaseTool
from langchain_anthropic import ChatAnthropic
from langchain_community.document_transformers import Html2TextTransformer
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
from langchain_community.document_loaders.url_playwright import PlaywrightURLLoader

token_counting_llm = ChatAnthropic(
    model_name="claude-3-haiku-20240307",
)

output_parser = StrOutputParser()

llm = ChatAnthropic(
    model_name="claude-3-haiku-20240307",
    temperature=0.2,
    # Discord has a max of 2000 words so we attempt to keep the token count down to below that.
    max_tokens_to_sample=400,
)

search_term_chain = ChatPromptTemplate.from_messages([
    ("system", """
    You will recieve a message from discord. Your task is to generate a query for a search engine that will help another AI generate an answer (which will be Minecraft: Java Edition related). You are forbidden from using punctuation or numbers of any kind in the search term. Always return at least one or more words, even if it doesn't make sense to do so.
    """),
    ("user", "{input}"),
]) | llm | output_parser


@tool
async def search(query: str):
    """Search the internet only to find out more about playing Minecraft Java Edition or Minecraft Java Edition in general.
    
    Note: all queries should relate to Minecraft Java Edition. If a query does not appear to be about Minecraft Java Edition, put 'Minecraft Java Edition' at the end of the query.
    """
    print("searching the internet...")
    search_api = DuckDuckGoSearchAPIWrapper()
    # search_term = await search_term_chain.ainvoke({"input": prompt})
    # if search_term == '':
    #     # If there's no search term, the AI hasn't found anything to search for.
    #     return ("", [])
    # print(f"Search term: {search_term}")
    search_results = search_api.results(query=query, max_results=3)
    # search_result = search.run(search_term)
    # OK, now we download the results and return them with aiohttp
    results_text = []
    urls = [r['link'] for r in search_results]
    loader = PlaywrightURLLoader(
        urls,
        continue_on_failure=True,
        headless=True,
        )
    docs = await loader.aload()

    html2text = Html2TextTransformer()
    docs_transformed = html2text.transform_documents(docs)
    for d, url in zip(docs_transformed, urls):
        results_text.append('From URL: ' + url + '\n' + d.page_content)

    results_text_concat = "\n\n".join(results_text)


    # This is a lazy way to get the context window down to a managable size, but
    # this is a toy bot so it doesn't matter if the context isn't well formed
    while token_counting_llm.get_num_tokens(results_text_concat) > 100_000:
        results_text_concat = results_text_concat[:-100]

    # TODO add URLS to this string
    return results_text_concat


import googleapiclient.discovery
import time

LEASE_TIME_IN_SECONDS: int = 0
SERVER_IS_ON = False

@tool
async def turn_minecraft_server_on_or_off(switch_on: bool):
    """
    Turns the Minecraft server on or off.
    """
    global LEASE_TIME_IN_SECONDS, SERVER_IS_ON

    if switch_on:
        print("Turned on the Minecraft server.")
        async def turn_off_server():
            global LEASE_TIME_IN_SECONDS, SERVER_IS_ON
            while LEASE_TIME_IN_SECONDS > 0:
                asyncio.sleep(1)
                LEASE_TIME_IN_SECONDS -= 1
                print(f"Server will turn off in {LEASE_TIME_IN_SECONDS} seconds.")

            await turn_minecraft_server_on_or_off(False)

        # If the server is not on, it's about to be switched on so schedule it
        # to switch off later. If the server is on, then it's already scheduled
        # to switch off, we just renew the lease time to be 2 hours.
        LEASE_TIME_IN_SECONDS = 60 * 60* 2 # 2 hours
        if not SERVER_IS_ON:
            asyncio.create_task(turn_off_server())

    SERVER_IS_ON = switch_on

    compute = googleapiclient.discovery.build('compute', 'v1')

    project = 'i-hexagon-304409'
    zone = 'europe-west1-b'
    instance_group = 'minecraft-instance-group-1'

    request = compute.instanceGroupManagers().resize(
        project=project,
        zone=zone,
        instanceGroupManager=instance_group,
        size=1 if switch_on else 0,
    ).execute()


    return f"Turned {'on' if switch_on else 'off'} the Minecraft server."
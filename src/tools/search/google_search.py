from typing import List
from dotenv import load_dotenv
load_dotenv(verbose=True)

import requests
import os

from src.tools.search.base import WebSearchEngine, SearchItem
from src.proxy import PROXY_URL, proxy_env

def search(params):
    """
    Mock function to simulate Google search results.
    In a real-world scenario, this would interface with the Google Search API.
    """
    with proxy_env():
        base_url = os.getenv("SKYWORK_GOOGLE_SEARCH_API")
        response = requests.get(base_url, params=params)
    return response

class GoogleSearchEngine(WebSearchEngine):
    async def perform_search(
        self,
        query: str,
        num_results: int = 10,
        filter_year: int = None,
        *args, **kwargs
    ) -> List[SearchItem]:
        """
        Google search engine.

        Returns results formatted according to SearchItem model.
        """
        params = {
            "q": query,
            "num": num_results,
        }
        if filter_year is not None:
            params["tbs"] = f"cdr:1,cd_min:01/01/{filter_year},cd_max:12/31/{filter_year}"

        response = search(params)

        if response.status_code == 200:
            items = response.json()
        else:
            raise ValueError(response.json())

        if "organic" not in items.keys():
            if filter_year is not None:
                raise Exception(
                    f"No results found for query: '{query}' with filtering on year={filter_year}. Use a less restrictive query or do not filter on year."
                )
            else:
                raise Exception(f"No results found for query: '{query}'. Use a less restrictive query.")

        results = []
        if "organic" in items:
            for idx, page in enumerate(items["organic"]):
                title = page.get("title", f"Google Result {idx + 1}")
                url = page.get("link", "")
                position = page.get("position", idx + 1)
                description = page.get("snippet", None)
                date = page.get("date", None)
                source = page.get("source", None)

                results.append(
                    SearchItem(
                        title=title,
                        url=url,
                        date=date,
                        position=position,
                        source=source,
                        description=description,
                    )
                )

        return results
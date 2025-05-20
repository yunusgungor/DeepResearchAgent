import warnings
warnings.simplefilter("ignore", DeprecationWarning)

import os
import sys
from pathlib import Path
import asyncio

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.tools.web_searcher import WebSearcherTool


if __name__ == "__main__":
    web_search = WebSearcherTool()
    web_search.fetch_content = True

    task = """
    If Eliud Kipchoge could maintain his record-making marathon pace indefinitely, how many thousand hours would it take him to run the distance between the Earth and the Moon its closest approach? Please use the minimum perigee value on the Wikipedia page for the Moon when carrying out your calculation. Round your result to the nearest 1000 hours and do not use any comma separators if necessary.
    """
    instruct = "Please planning the solution step by step and return the final answer only. Do not include any intermediate steps in your final answer."


    search_response = asyncio.run(web_search.forward(
        query=task,
    ))
    print(search_response.output)
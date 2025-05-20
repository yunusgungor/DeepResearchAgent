import warnings
warnings.simplefilter("ignore", DeprecationWarning)

import os
import sys
from pathlib import Path
import asyncio

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.tools.deep_analyzer import DeepAnalyzerTool

if __name__ == "__main__":
    deep_analyzer = DeepAnalyzerTool()

    task = """
    Please give the result of the following task:
    2x + 3 = 11,
    x = ?
    """

    response = asyncio.run(deep_analyzer.forward(task=task))
    
    print(response)
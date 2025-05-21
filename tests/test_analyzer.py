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
    Please analyze the attached file or uri and provide a detailed caption.
    """

    response = asyncio.run(deep_analyzer.forward(task=task, source="/Users/wentaozhang/workspace/RA/AgentScope/data/hle/images/test/6687ffb1091058ff19128813.png"))
    
    print(response)
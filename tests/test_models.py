import warnings
warnings.simplefilter("ignore", DeprecationWarning)

import os
import sys
from pathlib import Path
import asyncio

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.models import model_manager
from src.tools.deep_analyzer import DeepAnalyzerTool

if __name__ == "__main__":
    model_manager.init_models(use_local_proxy=False)
    
    messages = [
        {
            "role": "user",
            "content": "What is the capital of France?"
        }
    ]
    
    response = asyncio.run(model_manager.registed_models["claude37-sonnet-thinking"](
        messages=messages,
    ))
    print(response)
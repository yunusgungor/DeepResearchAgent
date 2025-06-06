import warnings
warnings.simplefilter("ignore", DeprecationWarning)

import os
import sys
from pathlib import Path
import asyncio

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.tools.python_interpreter import PythonInterpreterTool
from src.models import model_manager

if __name__ == "__main__":
    model_manager.init_models(use_local_proxy=False)
    
    pit = PythonInterpreterTool()
    code = """
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    else:
        fib_sequence = [0, 1]
        for i in range(2, n):
            fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
        return fib_sequence
result = fibonacci(10)
    """
    content = asyncio.run(pit.forward(code))
    print(content)
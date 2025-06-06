import warnings
import os
warnings.simplefilter("ignore", DeprecationWarning)

import sys
from pathlib import Path
import asyncio

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.tools.markdown.mdconvert import MarkitdownConverter
from src.models import model_manager

if __name__ == "__main__":
    model_manager.init_models(use_local_proxy=True)
    
    mdconvert = MarkitdownConverter()
    md = mdconvert.convert(os.path.join(root, "data/GAIA/2023/validation/366e2f2b-8632-4ef2-81eb-bc3877489217.pdf"))
    print(md)

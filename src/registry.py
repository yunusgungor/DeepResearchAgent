from typing import List, Dict, Any

REGISTED_MODELS: Dict[str, Any] = {}

def register_model(model_id: str, model: Any) -> None:
    """Register a model with a unique ID."""
    if model_id in REGISTED_MODELS:
        raise ValueError(f"Model ID '{model_id}' is already registered.")
    REGISTED_MODELS[model_id] = model
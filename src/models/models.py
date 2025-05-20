import os
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv(verbose=True)
from src.config import config
from src.logger import logger
from src.models.litellm import LiteLLMModel
from src.models.openaillm import OpenAIServerModel
from src.registry import REGISTED_MODELS

custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}

use_local_proxy = config.use_local_proxy
if use_local_proxy:
    logger.info("Using local proxy")
    from src.proxy.local_proxy import PROXY_URL, HTTP_CLIENT, ASYNC_HTTP_CLIENT

    # gpt-4o
    model_name = "gpt-4o"
    model_id = "openai/gpt-4o"
    client = OpenAI(
        api_key=os.getenv("SKYWORK_API_KEY"),
        base_url=os.getenv("SKYWORK_API_BASE"),
        http_client=HTTP_CLIENT,
    )
    model = LiteLLMModel(
        model_id=model_id,
        http_client=client,
        custom_role_conversions=custom_role_conversions,
    )
    REGISTED_MODELS[model_name] = model

    # gpt-4.1
    model_name = "gpt-4.1"
    model_id = "openai/gpt-4.1"
    client = OpenAI(
        api_key=os.getenv("SKYWORK_API_KEY"),
        base_url=os.getenv("SKYWORK_API_BASE"),
        http_client=HTTP_CLIENT,
    )
    model = LiteLLMModel(
        model_id=model_id,
        http_client=client,
        custom_role_conversions=custom_role_conversions,
    )
    REGISTED_MODELS[model_name] = model

    # o1
    model_name = "o1"
    model_id = "openai/o1"
    client = OpenAI(
        api_key=os.getenv("SKYWORK_API_KEY"),
        base_url=os.getenv("SKYWORK_API_BASE"),
        http_client=HTTP_CLIENT,
    )
    model = LiteLLMModel(
        model_id=model_id,
        http_client=client,
        custom_role_conversions=custom_role_conversions,
    )
    REGISTED_MODELS[model_name] = model

    # o3
    model_name = "o3"
    model_id = "openai/o3"
    client = OpenAI(
        api_key=os.getenv("SKYWORK_API_KEY"),
        base_url=os.getenv("SKYWORK_AZURE_HK_API_BASE"),
        http_client=HTTP_CLIENT,
    )
    model = LiteLLMModel(
        model_id=model_id,
        http_client=client,
        custom_role_conversions=custom_role_conversions,
    )
    REGISTED_MODELS[model_name] = model

    # wisper
    model_name = "whisper"
    model_id = "openai/whisper"
    client = OpenAI(
        api_key=os.getenv("SKYWORK_API_KEY"),
        base_url=os.getenv("SKYWORK_AZURE_HK_API_BASE"),
        http_client=HTTP_CLIENT,
    )
    model = LiteLLMModel(
        model_id=model_id,
        http_client=client,
        custom_role_conversions=custom_role_conversions,
    )
    REGISTED_MODELS[model_name] = model

    # claude37-sonnet
    model_name = "claude37-sonnet"
    model_id = "claude37-sonnet"
    client = OpenAI(
        api_key=os.getenv("SKYWORK_API_KEY"),
        base_url=os.getenv("SKYWORK_API_BASE"),
        http_client=HTTP_CLIENT,
    )
    model = OpenAIServerModel(
        model_id=model_id,
        http_client=client,
        custom_role_conversions=custom_role_conversions,
    )
    REGISTED_MODELS[model_name] = model

    # gemini-2.5-pro
    model_name = "gemini-2.5-pro"
    model_id = "gemini-2.5-pro-preview-05-06"
    client = OpenAI(
        api_key=os.getenv("SKYWORK_API_KEY"),
        base_url=os.getenv("SKYWORK_GOOGLE_API_BASE"),
        http_client=HTTP_CLIENT,
    )
    model = OpenAIServerModel(
        model_id=model_id,
        http_client=client,
        custom_role_conversions=custom_role_conversions,
    )
    REGISTED_MODELS[model_name] = model

    # gpt-4o-search-preview
    model_name = "gpt-4o-search-preview"
    model_id = "gpt-4o-search-preview"
    client = OpenAI(
        api_key=os.getenv("SKYWORK_API_KEY"),
        base_url=os.getenv("SKYWORK_OPENROUTER_US_API_BASE"),
        http_client=HTTP_CLIENT,
    )
    model = OpenAIServerModel(
        model_id=model_id,
        http_client=client,
        custom_role_conversions=custom_role_conversions,
    )
    REGISTED_MODELS[model_name] = model

    # claude37-sonnet-thinking
    model_name = "claude37-sonnet-thinking"
    model_id = "claude-3.7-sonnet-thinking"
    client = OpenAI(
        api_key=os.getenv("SKYWORK_API_KEY"),
        base_url=os.getenv("SKYWORK_OPENROUTER_US_API_BASE"),
        http_client=HTTP_CLIENT,
    )
    model = OpenAIServerModel(
        model_id=model_id,
        http_client=client,
        custom_role_conversions=custom_role_conversions,
    )
    REGISTED_MODELS[model_name] = model

    logger.info("Local models registered, support models: %s", ", ".join(REGISTED_MODELS.keys()))
else:
    logger.info("Not using local proxy")
    # gpt-4o
    model_name = "gpt-4o"
    model_id = "openai/gpt-4o"
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    model = LiteLLMModel(
        model_id=model_id,
        http_client=client,
        custom_role_conversions=custom_role_conversions,
    )
    REGISTED_MODELS[model_name] = model

        # gpt-4.1
    model_name = "gpt-4.1"
    model_id = "openai/gpt-4.1"
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    model = LiteLLMModel(
        model_id=model_id,
        http_client=client,
        custom_role_conversions=custom_role_conversions,
    )
    REGISTED_MODELS[model_name] = model

    # o3
    model_name = "o3"
    model_id = "openai/o3"
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    model = LiteLLMModel(
        model_id=model_id,
        http_client=client,
        custom_role_conversions=custom_role_conversions,
    )
    REGISTED_MODELS[model_name] = model

    logger.info("Remote models registered, support models: %s", ", ".join(REGISTED_MODELS.keys()))

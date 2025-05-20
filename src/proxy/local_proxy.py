import os
import httpx
import openai
import contextlib
from dotenv import load_dotenv

load_dotenv(verbose=True)

PROXY_URL = os.getenv('LOCAL_PROXY_BASE') # http://localhost:6655
TRANSPORT = httpx.HTTPTransport(proxy=httpx.Proxy(url=PROXY_URL))
HTTP_CLIENT = httpx.Client(transport=TRANSPORT)

ASYNC_TRANSPORT = httpx.AsyncHTTPTransport(proxy=httpx.Proxy(url=PROXY_URL))
ASYNC_HTTP_CLIENT = httpx.AsyncClient(transport=ASYNC_TRANSPORT)

@contextlib.contextmanager
def proxy_env(proxy_url: str = PROXY_URL):
    os.environ["HTTP_PROXY"] = proxy_url
    os.environ["HTTPS_PROXY"] = proxy_url
    try:
        yield
    finally:
        del os.environ["HTTP_PROXY"]
        del os.environ["HTTPS_PROXY"]

__all__ = [
    "PROXY_URL",
    "HTTP_CLIENT",
    "ASYNC_HTTP_CLIENT",
]
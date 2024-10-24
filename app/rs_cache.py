"""Cache Plugin.

app/cache.py

"""
import os
import pickle
from cashews import cache

from fastapi import Response
from fastapi.responses import StreamingResponse, ORJSONResponse


async def make_cached_data(response: StreamingResponse):
    content = b""
    async for chunk in response.body_iterator:
        content += chunk

    if response.media_type == 'application/json':
        response_cls = ORJSONResponse
    else:
        response_cls = Response

    return response_cls(
        status_code=response.status_code,
        content=content,
        headers=response.headers,
        media_type=response.media_type,
        background=response.background,
    )

async def read_cache(key):
    value = await cache.get_raw(key)
    if value is not None:
        print(f"read cache")
        response = pickle.loads(value)
        response.headers["X-Cache"] = "HIT"
        return response
    return None

async def write_cache(key, response: StreamingResponse):
    response = await make_cached_data(response)
    serialized_result = pickle.dumps(response)
    print(f"write cache")
    await cache.set_raw(key, serialized_result, expire=3600)
    response.headers["X-Cache"] = "MISS"
    return response

def setup_cache():
    cache.setup(os.environ.get("CACHE_ENDPOINT", "mem://"))
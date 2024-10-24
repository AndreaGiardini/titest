"""app

app/main.py

"""

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from . import rs_cache
from .rs_cache import setup_cache

from titiler.application import main as titiler_app_main
from fastapi import Request

app = titiler_app_main.app

# Setup Cache on Startup
app.add_event_handler("startup", setup_cache)
add_exception_handlers(app, DEFAULT_STATUS_CODES)

@app.middleware("tile-cache")
async def add_tile_cache(request: Request, call_next):

    key = f"{request.url.path}:{request.query_params}"
    if 'tile' in request.url.path:
        res = await rs_cache.read_cache(key)
        # Cached request
        if res is not None:
            return res

    # Uncached request
    response = await call_next(request)

    if 'tile' in request.url.path:
        return await rs_cache.write_cache(key, response)
    return response


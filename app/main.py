"""app

app/main.py

"""

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.mosaic.factory import MosaicTilerFactory

from .cache import setup_cache, cached
from .routes import cog

from titiler.application import main as titiler_app_main

app = titiler_app_main.app

# Setup Cache on Startup
app.add_event_handler("startup", setup_cache)
add_exception_handlers(app, DEFAULT_STATUS_CODES)

#print(app.routes)

for route in app.routes:
    if 'tile' in route.path:
        # Add decorator to APIRoute
        print(route)
        #app.routes.remove(route)
        cached_route = cached(alias="default")(route)
        app.routes.remove(route)
        #app.routes.append(cached_route)

#app.router.routes
#app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])

# mosaic = MosaicTilerFactory(router_prefix="/mosaicjson")
# print(mosaic.router.routes)
# app.include_router(
#     mosaic.router,
#     prefix="/mosaicjson",
#     tags=["MosaicJSON"],
# )

"""routes.

app/routes.py
"""
from dataclasses import dataclass
from typing import Callable, Dict, Type, Literal, List, Tuple, Optional
from urllib.parse import urlencode

from fastapi import Depends, Path, Query
from starlette.requests import Request
from starlette.responses import Response

from morecantile import TileMatrixSet
from rio_tiler.io import BaseReader, Reader

from titiler.core.factory import img_endpoint_params
from titiler.core.factory import TilerFactory as TiTilerFactory
from titiler.core.dependencies import RescalingParams
from titiler.core.models.mapbox import TileJSON
from titiler.core.resources.enums import ImageType

#from .cache import cached


@dataclass
class TilerFactory(TiTilerFactory):

    reader: Type[BaseReader] = Reader

    def register_routes(self):
        """This Method register routes to the router."""

        @self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
        )
        # Add default cache config dictionary into cached alias.
        # Note: if alias is used, other arguments in cached will be ignored. Add other arguments into default dicttionary in setup_cache function.
        @cached(alias="default")
        def tile(
            z: int = Path(..., ge=0, le=30, description="TMS tiles's zoom level"),
            x: int = Path(..., description="TMS tiles's column"),
            y: int = Path(..., description="TMS tiles's row"),
            tileMatrixSetId: Literal[tuple(self.supported_tms.list())] = Path(
                #self.default_tms,
                description=f"TileMatrixSet Name (default: '{self.default_tms}')",
            ),
            scale: int = Path(
                #1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            format: ImageType = Path(
                #None, description="Output image type. Default is auto."
                description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            buffer: Optional[float] = Query(
                None,
                gt=0,
                title="Tile buffer.",
                description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
            ),
            post_process=Depends(self.process_dependency),
            rescale: Optional[List[Tuple[float, ...]]] = Depends(RescalingParams),
            color_formula: Optional[str] = Query(
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
        ):
            """Create map tile from a dataset."""
            tms = self.supported_tms.get(tileMatrixSetId)

            with self.reader(src_path, tms=tms, **reader_params) as src_dst:
                image = src_dst.tile(
                    x,
                    y,
                    z,
                    tilesize=scale * 256,
                    buffer=buffer,
                    **layer_params,
                    **dataset_params,
                )
                dst_colormap = getattr(src_dst, "colormap", None)


            if post_process:
                image = post_process(image)

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            if cmap := colormap or dst_colormap:
                image = image.apply_colormap(cmap)

            if not format:
                format = ImageType.jpeg if image.mask.all() else ImageType.png

            content = image.render(
                img_format=format.driver,
                **format.profile,
                **render_params,
            )

            return Response(content, media_type=format.mediatype)

        @self.router.get(
            "/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @self.router.get(
            "/{tileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @cached(alias="default")
        def tilejson(
            request: Request,
            tileMatrixSetId: Literal[tuple(self.supported_tms.list())] = Path(
                #self.default_tms,
                description=f"TileMatrixSet Name (default: '{self.default_tms}')",
            ),
            src_path=Depends(self.path_dependency),
            tile_format: Optional[ImageType] = Query(
                None, description="Output image type. Default is auto."
            ),
            tile_scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            minzoom: Optional[int] = Query(
                None, description="Overwrite default minzoom."
            ),
            maxzoom: Optional[int] = Query(
                None, description="Overwrite default maxzoom."
            ),
            layer_params=Depends(self.layer_dependency),  # noqa
            dataset_params=Depends(self.dataset_dependency),  # noqa
            buffer: Optional[float] = Query(  # noqa
                None,
                gt=0,
                title="Tile buffer.",
                description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
            ),
            post_process=Depends(self.process_dependency),  # noqa
            rescale: Optional[List[Tuple[float, ...]]] = Depends(
                RescalingParams
            ),  # noqa
            color_formula: Optional[str] = Query(  # noqa
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
            colormap=Depends(self.colormap_dependency),  # noqa
            render_params=Depends(self.render_dependency),  # noqa
            reader_params=Depends(self.reader_dependency),
        ):
            """Return TileJSON document for a dataset."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "tileMatrixSetId": tileMatrixSetId,
            }
            if tile_format:
                route_params["format"] = tile_format.value

            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            tms = self.supported_tms.get(tileMatrixSetId)
            with self.reader(src_path, tms=tms, **reader_params) as src_dst:
                return {
                    "bounds": src_dst.geographic_bounds,
                    "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                    "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                    "tiles": [tiles_url],
                }

        # Register Map viewer
        self.map_viewer()


cog = TilerFactory()
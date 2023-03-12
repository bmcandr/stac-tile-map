from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from settings import settings

from stac_tiler_map import create_stac_tiler_map


class MapInputs(BaseModel):
    geojson_file: str = settings.DEFAULT_GEOJSON
    catalog: str = settings.DEFAULT_CATALOG
    collection: str = settings.DEFAULT_COLLECTION
    asset_key: str = settings.DEFAULT_ASSET_KEY
    name_key: str = settings.DEFAULT_NAME_KEY
    search_period: int = settings.DEFAULT_SEARCH_PERIOD


def app_factory() -> FastAPI:
    app = FastAPI()

    @app.get("/root", response_class=HTMLResponse)
    async def root():
        m = create_stac_tiler_map(**MapInputs().dict())

        return HTMLResponse(m.get_root().render())

    @app.get("/custom", response_class=HTMLResponse)
    async def create_custom_map(inputs: MapInputs):
        m = create_stac_tiler_map(**inputs.dict())

        return HTMLResponse(m.get_root().render())

    return app


app = app_factory()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)

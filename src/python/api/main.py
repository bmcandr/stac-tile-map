from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from settings import settings
from stac_tiler_map.create_map import create_stac_tiler_map

app = FastAPI()


class MapInputs(BaseModel):
    geojson_file: str = settings.DEFAULT_GEOJSON
    catalog: str = settings.DEFAULT_CATALOG
    collection: str = settings.DEFAULT_COLLECTION
    asset_key: str = settings.DEFAULT_ASSET_KEY
    name_key: str = settings.DEFAULT_NAME_KEY
    search_period: int = settings.DEFAULT_SEARCH_PERIOD


@app.get("/", response_class=HTMLResponse)
async def root():
    m = create_stac_tiler_map(**MapInputs().dict())

    return HTMLResponse(m.get_root().render())


@app.get("/custom", response_class=HTMLResponse)
async def create_custom_map(inputs: MapInputs):
    m = create_stac_tiler_map(**inputs.dict())

    return HTMLResponse(m.get_root().render())

from fastapi import APIRouter, Depends, FastAPI
from fastapi.responses import HTMLResponse
from schemas import Inputs

from stac_tiler_map import create_stac_tiler_map


def app_factory() -> FastAPI:
    app = FastAPI(title="STAC+GeoJSON+COG+Tiler Demo")

    @app.get("/map", tags=["maps"], response_class=HTMLResponse)
    async def create_map(inputs: Inputs = Depends()):
        m = create_stac_tiler_map(inputs)

        return HTMLResponse(m.get_root().render())

    return app


app = app_factory()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)

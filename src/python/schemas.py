from pydantic import AnyHttpUrl, BaseModel


class Inputs(BaseModel):
    geojson_path: str = "data/national-parks.geojson"
    catalog: AnyHttpUrl = "https://earth-search.aws.element84.com/v1"
    collection: str = "sentinel-2-l2a"
    asset_key: str = "visual"
    search_period: int = 30

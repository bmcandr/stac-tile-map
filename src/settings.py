from pydantic import BaseSettings


class Settings(BaseSettings):
    DEFAULT_GEOJSON: str = "data/national-parks.geojson"
    DEFAULT_CATALOG: str = "https://earth-search.aws.element84.com/v1"
    DEFAULT_COLLECTION: str = "sentinel-2-l2a"
    DEFAULT_ASSET_KEY: str = "visual"
    DEFAULT_NAME_KEY: str = "Name"
    DEFAULT_SEARCH_PERIOD: int = 30


settings = Settings()

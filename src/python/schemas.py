from pathlib import Path
from typing import Union

from pydantic import AnyHttpUrl, BaseModel, FilePath


class Inputs(BaseModel):
    geojson: Union[FilePath, AnyHttpUrl] = Path("data", "national-parks.geojson")
    catalog: AnyHttpUrl = "https://earth-search.aws.element84.com/v1"
    collection: str = "sentinel-2-l2a"
    asset_key: str = "visual"
    search_period: int = 30


class CliInputs(Inputs):
    output_file: Union[FilePath, AnyHttpUrl] = Path("map.html")

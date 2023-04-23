from typing import Dict, List, Union

from pydantic import AnyHttpUrl, BaseModel, Field


class Inputs(BaseModel):
    geojson_path: str = Field(
        description="A URL to a GeoJSON file",
        default="https://raw.githubusercontent.com/martynafford/natural-earth-geojson/master/110m/cultural/ne_110m_populated_places.json",
    )
    catalog: AnyHttpUrl = Field(
        description="A URL to a STAC catalog",
        default="https://earth-search.aws.element84.com/v1",
    )
    collection: str = Field(
        description="The name of the STAC collection to search",
        default="sentinel-2-l2a",
    )
    asset_key: str = Field(
        description="The asset key of the COG to display", default="visual"
    )
    search_period: int = Field(
        description="The period (in days) to search backwards starting from today",
        default=30,
    )
    query: Dict[str, Dict[str, Union[int, float, str]]] = Field(
        default={
            "s2:nodata_pixel_percentage": {"gte": 0, "lte": 10},
            "eo:cloud_cover": {"gte": 0, "lte": 10},
        }
    )
    sort_on: List[str] = Field(default=["s2:nodata_pixel_percentage", "eo:cloud_cover"])

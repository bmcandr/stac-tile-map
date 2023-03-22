import geopandas as gpd
import pandas as pd
import re
from slugify import slugify

"""
Read tables of terrestrial impact craters from Wikipedia
and convert to a GeoJSON.
"""

raw_dfs = pd.read_html(
    "https://en.wikipedia.org/wiki/List_of_impact_craters_on_Earth", match="Coordinates"
)

# combine tables
crater_df = pd.concat(raw_dfs)

# normalize columns and remove duplicates
crater_df.columns = [slugify(column, separator="_") for column in crater_df.columns]
crater_df.drop("age_million_years", axis=1, inplace=True)


def clean_coords(s: str) -> str:
    """Parse decimal degree coordinates from coordinate string"""

    pattern = re.compile("[0-9]+[.][0-9]+°[NS] [0-9]+[.][0-9]+°[EW]")
    match = re.search(pattern, s)

    if match is None:
        raise ValueError(f"No match found in {s}")

    return match.group(0)


crater_df["coordinates"] = crater_df["coordinates"].apply(clean_coords)


def floatify_coord(coord_str: str) -> float:
    coord = float(coord_str[:-2])

    return coord if coord_str[-1] in ["E", "N"] else -coord


def parse_lat(coord: str) -> float:
    lat_str = coord.split(" ")[0]

    return floatify_coord(lat_str)


def parse_lon(coord: str) -> float:
    lon_str = coord.split(" ")[1]

    return floatify_coord(lon_str)


# create lon and lat columns from coordinates column
crater_df["lat"] = crater_df["coordinates"].apply(parse_lat)
crater_df["lon"] = crater_df["coordinates"].apply(parse_lon)

# create GeoDataFrame
crater_gdf = gpd.GeoDataFrame(
    data=crater_df, geometry=gpd.points_from_xy(crater_df.lon, crater_df.lat)
)

# drop extraneous columns
crater_gdf.drop(["coordinates", "lat", "lon"], axis=1, inplace=True)

# write to GeoJSON file
crater_gdf.to_file("data/craters.geojson")

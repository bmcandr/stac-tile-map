import logging
import random
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Tuple, Union

import folium
import folium.features
import geojson
import pystac
import pystac_client
import requests
from dateutil import parser
from schemas import Inputs
from shapely import geometry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

DATE_FMT = "%Y-%m-%d"


def read_geojson(path: str) -> geojson.FeatureCollection:
    """Read a local or remote GeoJSON file.

    If the file contains only a Geometry, it is converted to
    a FeatureCollection.

    Parameters
    ----------
    path : str
        Path or URL to a GeoJSON file.

    Returns
    -------
    geojson.FeatureCollection
        A GeoJSON FeatureCollection object.
    """
    if path.startswith(("http", "www")):
        resp = requests.get(url=path)
        resp.raise_for_status()

        geojson_obj = geojson.loads(resp.text)

    else:
        with open(path, "r") as f:
            geojson_obj = geojson.load(f)

    if not isinstance(geojson_obj, geojson.FeatureCollection):
        geojson_obj = geojson.FeatureCollection(features=[geojson_obj])

    return geojson_obj


def get_search_dates(end_date: Union[date, datetime], period: int = 1) -> str:
    """Generate a STAC search compliant datetime string (e.g., "2022-12-01/2023-01-01").
    Search start date is calculated by subtracting the period in days from the end date.

    Parameters
    ----------
    end_date : datetime
        The end date of the search period.
    period : int, optional
        Search period in days, by default 1.

    Returns
    -------
    str
        A STAC search compliant datetime string (e.g., "2022-12-01/2023-01-01").
    """

    search_period = timedelta(days=period)
    start_date = end_date - search_period

    return f"{start_date:{DATE_FMT}}/{end_date:{DATE_FMT}}"


def get_items(
    stac_client: pystac_client.Client,
    collection: str,
    end_date: datetime,
    search_period: int,
    intersects: Dict,
    query: Dict[str, Dict[str, Any]] = {},
    search_loops: int = 12,
) -> Union[pystac.ItemCollection, None]:
    """Searches the STAC collection for an Item that matches the criteria.
    If nothing found in first search, search iterates backwards in time
    by search period (and lightly loosens cloud cover query criteria).

    Parameters
    ----------
    stac_client : pystac_client.Client
        A STAC client.
    collection : str
        STAC collection to search.
    end_date : datetime
        End date of the search period (e.g., today)
    search_period : int
        Length of search period (in days).
    intersects : Dict
        GeoJSON geometry or object that implements __geo_interface__
    query : Dict[str, Dict[str, Any]]
        A STAC compliant search query. Defaults to `{}`.

    Returns
    -------
    pystac.Item
        A STAC Item that meets the search criteria.
    """

    item_collection = None
    for _ in range(search_loops):
        date_range = get_search_dates(end_date=end_date, period=search_period)
        logger.info(
            f"Searching date range {date_range} {f'with query {query}' if query else ''}"
        )

        search = stac_client.search(
            collections=[collection],
            datetime=date_range,
            intersects=intersects,
            query=query,
        )

        item_collection = search.item_collection()

        if item_collection:
            break

        # search prior period
        end_date = end_date - timedelta(days=search_period)

    if not item_collection:
        logger.info("No scenes found!")

    logger.info("Scenes found!")
    return item_collection


def sort_items(
    item_collection: pystac.ItemCollection,
    sort_on: List[str],
    ascending: bool = True,
) -> List[pystac.Item]:
    return sorted(
        item_collection,
        key=lambda item: [item.properties[property] for property in sort_on],
        reverse=(not ascending),
    )


def _create_map(
    center: Tuple[float, float], basemap: str = "cartodbpositron", zoom: int = 10
) -> folium.Map:
    """Create a folium map.

    Parameters
    ----------
    center : Tuple[float, float]
        (lon, lat) to center map on.
    basemap : str, optional
        One of folium's built-in basemap tilesets, by default "cartodbpositron"
    zoom : int, optional
        Zoom level, by default 10

    Returns
    -------
    folium.Map
        A map object.
    """

    return folium.Map(
        location=center,
        tiles=basemap,
        zoom_start=zoom,
    )


def _create_tile_layer_from_item(
    item: pystac.Item,
    asset_key: str,
    tiler_url: str = "https://api.cogeo.xyz/cog/tiles/{z}/{x}/{y}",
) -> folium.TileLayer:
    """Create a map tile layer from a COG-containing STAC Item.

    Parameters
    ----------
    item : pystac.Item
        STAC Item with COG asset to add to tile layer.
    asset_key : str
        Key of asset to tile on layer.
    tiler_url : str, optional
        URL to the tiler, defaults to DevSeed's awesome free tiler "https://api.cogeo.xyz/cog/tiles/{z}/{x}/{y}".

    Returns
    -------
    folium.TileLayer
        Tile layer displaying COG asset.
    """

    virtual_tiles = f"{tiler_url}?url={item.assets[asset_key].href}"
    return folium.TileLayer(
        tiles=virtual_tiles, name="COG", overlay=True, attr="IndigoAg"
    )


def _add_stac_info_to_feature(feature: Dict, item: pystac.Item, asset_key: str) -> Dict:
    """Adds link to STAC Item and asset download to feature.

    Parameters
    ----------
    feature : Dict
        GeoJSON Feature dictionary.
    item : pystac.Item
        STAC Item to extract information from.
    asset_key : str
        Key to asset in STAC Item.

    Returns
    -------
    Dict
        Dictionary of formatted information about feature and STAC Item.
    """

    link_str = "<a target='_blank' href={href}>{label}</a>"

    item_id = item.id
    item_href = item.self_href
    asset_href = item.assets[asset_key].href
    date = parser.parse(item.properties["datetime"]).date()

    update_dict = {
        "Date": date.strftime("%Y-%m-%d"),
        "STAC Item": link_str.format(href=item_href, label=item_id),
        "Download": link_str.format(href=asset_href, label="click here"),
    }

    feature["properties"].update(update_dict)

    return feature


def _create_geojson_layer(geojson: Dict, name: str) -> folium.GeoJson:
    """Create a folium layer from GeoJSON dictionary.

    Parameters
    ----------
    geojson : Dict
        A GeoJSON-like dictionary.
    name : str
        Layer name.

    Returns
    -------
    folium.GeoJson
        A GeoJSON map layer.
    """

    popup_fields = list(geojson["features"][0]["properties"].keys())
    return folium.GeoJson(
        geojson, name=name, popup=folium.GeoJsonPopup(fields=popup_fields)
    )


def create_stac_tiler_map(inputs: Inputs) -> folium.Map:
    """Creates a folium map object displaying a COG.

    Parameters
    ----------
    inputs : Inputs
        Map generation inputs.

    Returns
    -------
    folium.Map
        A map displaying COG and STAC info.
    """
    logger.info(f"Connecting to STAC Catalog: {inputs.catalog}")
    stac_client = pystac_client.Client.open(url=inputs.catalog, ignore_conformance=True)

    logger.info(f"Selecting random feature from {inputs.geojson_path}")
    feature_collection = read_geojson(path=inputs.geojson_path)
    feature = feature_collection["features"][0]

    item_collection = None
    while not item_collection:
        feature = geojson.Feature(**random.choice(feature_collection["features"]))
        logger.info(f"Feature selected: {feature}")

        item_collection = get_items(
            stac_client=stac_client,
            collection=inputs.collection,
            end_date=datetime.utcnow(),
            search_period=inputs.search_period,
            intersects=feature["geometry"],
            query=inputs.query,
        )

    items = list(item_collection)

    if inputs.sort_on:
        items = sort_items(
            item_collection=item_collection, sort_on=inputs.sort_on, ascending=True
        )

    item = items[0]

    logger.info("Creating map")
    scene_centroid = geometry.shape(item.geometry).centroid
    m = _create_map(center=(scene_centroid.y, scene_centroid.x))

    logger.info(f"Adding scene {item.id} to map")
    tile_layer = _create_tile_layer_from_item(item=item, asset_key=inputs.asset_key)
    tile_layer.add_to(m)

    logger.info("Adding STAC info to feature")
    updated_feature = _add_stac_info_to_feature(
        feature=feature.copy(), item=item, asset_key=inputs.asset_key
    )
    logger.info("Adding GeoJSON layer to map")
    marker_layer = _create_geojson_layer(
        geojson=dict(features=[updated_feature]), name="Marker"
    )
    marker_layer.add_to(m)

    logger.info("Adding layer controls")
    folium.LayerControl().add_to(m)

    return m


__all__ = ["create_stac_tiler_map"]

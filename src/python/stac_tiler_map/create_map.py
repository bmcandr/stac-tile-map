import json
import logging
import os
import random
from datetime import datetime, timedelta
from typing import Dict, Tuple, Union

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


def read_geojson(path: str) -> geojson.FeatureCollection:
    """Read a local or remote GeoJSON file that contains
    a FeatureCollection.

    Parameters
    ----------
    path : str
        Path or URL pointing to a GeoJSON file that contains
        a FeatureCollection.

    Returns
    -------
    geojson.FeatureCollection
        A GeoJSON FeatureCollection.
    """
    if path.startswith(("http", "www")):
        resp = requests.get(url=path)
        resp.raise_for_status()

        geojson_obj = geojson.loads(resp.text)

    else:
        with open(path, "r") as f:
            geojson_obj = geojson.load(f)

    assert isinstance(geojson_obj, geojson.FeatureCollection)

    return geojson_obj


def _get_search_dates(end_date: datetime, period: int = 1) -> str:
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
    start_date_str, end_date_str = [
        datetime.strftime(date, "%Y-%m-%d") for date in [start_date, end_date]
    ]

    return f"{start_date_str}/{end_date_str}"


def _get_scene(
    stac_client: pystac_client.Client,
    collection: str,
    end_date: datetime,
    search_period: int,
    intersects: Dict,
) -> pystac.Item:
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

    Returns
    -------
    pystac.Item
        A STAC Item that meets the search criteria.
    """

    query_keys = ["s2:nodata_pixel_percentage", "eo:cloud_cover"]
    query_criteria = {"gte": 0, "lte": 10}
    query = {query_key: query_criteria for query_key in query_keys}

    scene_item = None
    while not scene_item:
        search_dates = _get_search_dates(end_date=end_date, period=search_period)
        logger.info(f"Searching date range {search_dates} with query {query}")

        search = stac_client.search(
            collections=[collection],
            datetime=search_dates,
            intersects=intersects,
            query=query,
        )

        scene_items = search.get_all_items()

        if scene_items:
            logger.info("Scenes found!")
            # sort by nodata and cloud cover
            scene_items = sorted(
                scene_items,
                key=lambda item: [
                    item.properties[query_key] for query_key in query_keys
                ],
            )

            scene_item = scene_items[0]
            break

        # loosen cloud cover criteria
        query["eo:cloud_cover"]["lte"] += 5
        # search prior period
        end_date = end_date - timedelta(days=search_period)

    return scene_item


def _create_map(
    location: Tuple[float, float], tiles: str = "cartodbpositron", zoom_start: int = 10
) -> folium.Map:
    """Create a folium map.

    Parameters
    ----------
    location : Tuple[float, float]
        (lon, lat) to center map on.
    tiles : str, optional
        One of folium's built-in tilesets, by default "cartodbpositron"
    zoom_start : int, optional
        Zoom level, by default 10

    Returns
    -------
    folium.Map
        A map object.
    """

    return folium.Map(
        location=location,
        tiles=tiles,
        zoom_start=zoom_start,
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
    feature = random.choice(feature_collection["features"])
    logger.info(f"Feature selected: {feature}")

    scene_item = _get_scene(
        stac_client=stac_client,
        collection=inputs.collection,
        end_date=datetime.utcnow(),
        search_period=inputs.search_period,
        intersects=feature["geometry"],
    )

    logger.info("Creating map")
    scene_centroid = geometry.shape(scene_item.geometry).centroid
    m = _create_map(location=(scene_centroid.y, scene_centroid.x))

    logger.info(f"Adding scene {scene_item.id} to map")
    tile_layer = _create_tile_layer_from_item(
        item=scene_item, asset_key=inputs.asset_key
    )
    tile_layer.add_to(m)

    logger.info("Adding STAC info to feature")
    updated_feature = _add_stac_info_to_feature(
        feature=feature.copy(), item=scene_item, asset_key=inputs.asset_key
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

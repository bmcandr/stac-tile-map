import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Tuple

import click
import folium
import folium.features
import pystac
import pystac_client
from shapely import geometry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


def _get_random_feature(geojson_fp: str) -> Dict:
    """Picks a random feature from a GeoJSON file.

    :param geojson_fp: Path to a GeoJSON file.
    :type geojson_fp: str
    :return: A dictionary containing a GeoJSON feature.
    :rtype: Dict
    """
    logger.info(f"Picking random feature from {geojson_fp}")
    with open(geojson_fp, "r") as fp:
        geojson = json.load(fp)

    features = geojson["features"]

    return random.choice(features)


def _get_search_dates(end_date: datetime, period: int = 1) -> str:
    """Generate a STAC search compliant datetime string (e.g., "2022-12-01/2023-01-01").
    Search start date is calculated by subtracting the period in days from the end date.

    :param end_date: The end date of the search period.
    :type end_date: datetime
    :param period: Search period in days, defaults to 1
    :type period: int, optional
    :return: A STAC search compliant datetime string (e.g., "2022-12-01/2023-01-01")
    :rtype: str
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

    :param stac_client: A STAC client.
    :type stac_client: pystac_client.Client
    :param collection: STAC collection to search.
    :type collection: str
    :param end_date: End date of the search period (e.g., today)
    :type end_date: datetime
    :param search_period: Length of search period in days.
    :type search_period: int
    :param intersects: GeoJSON geometry or object that implements __geo_interface__
    :type intersects: Dict
    :return: A pystac Item matching the search criteria, sorted by nodata percentage and cloud coverage.
    :rtype: pystac.Item
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

    :param location: (lon, lat) to center map on.
    :type location: Tuple[float, float]
    :param tiles: One of folium's built-in tilesets, defaults to "cartodbpositron"
    :type tiles: str, optional
    :param zoom_start: Zoom level, defaults to 10
    :type zoom_start: int, optional
    :return: A folium map object.
    :rtype: folium.Map
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

    :param item: STAC Item with COG asset to add to tile layer.
    :type item: pystac.Item
    :param asset_key: Key of asset to tile on layer.
    :type asset_key: str
    :param tiler_url: URL to the tiler, defaults to DevSeed's awesome free tiler "https://api.cogeo.xyz/cog/tiles/{z}/{x}/{y}"
    :type tiler_url: str, optional
    :return: Tile layer displaying COG asset.
    :rtype: folium.TileLayer
    """
    virtual_tiles = f"{tiler_url}?url={item.assets[asset_key].href}"
    return folium.TileLayer(
        tiles=virtual_tiles, name="COG", overlay=True, attr="IndigoAg"
    )


def _add_stac_info_to_feature(
    feature: Dict,
    item_id: str,
    item_href: str,
    asset_href: str,
) -> Dict:
    """Adds link to STAC Item and asset download to feature.

    :param feature: GeoJSON Feature dictionary.
    :type feature: Dict
    :param item_id: STAC Item ID.
    :type item_id: str
    :param item_href: Self link to STAC Item.
    :type item_href: str
    :param asset_href: Link to asset.
    :type asset_href: str
    :return: Updated feature with STAC properties.
    :rtype: Dict
    """
    link_str = "<a target='_blank' href={href}>{label}</a>"
    update_dict = {
        "STAC Item": link_str.format(href=item_href, label=item_id),
        "Download": link_str.format(href=asset_href, label="click here"),
    }
    feature["properties"].update(update_dict)
    return feature


def _create_geojson_layer(geojson: Dict, name: str) -> folium.GeoJson:
    """Create a folium layer from GeoJSON dictionary.

    :param geojson: A GeoJSON-like dictionary.
    :type geojson: Dict
    :param name: Layer name
    :type name: str
    :return: _description_
    :rtype: folium.GeoJson
    """
    popup_fields = list(geojson["features"][0]["properties"].keys())
    return folium.GeoJson(
        geojson, name=name, popup=folium.GeoJsonPopup(fields=popup_fields)
    )


@click.command()
@click.argument(
    "geojson_file",
    type=click.Path(exists=True, readable=True),
)
@click.argument("output_file", type=click.Path())
@click.option(
    "--catalog",
    default="https://earth-search.aws.element84.com/v1",
    help="URL to a public STAC Catalog",
)
@click.option(
    "--collection", default="sentinel-2-l2a", help="STAC Collection ID to search"
)
@click.option("--asset-key", default="visual", help="STAC asset key to add to map")
@click.option(
    "--name-key",
    default="Name",
    help="Key in feature properties to show in map marker popup",
)
@click.option("--search-period", default=30, help="Search period (in days)")
def main(
    geojson_file: str,
    output_file: str,
    catalog: str,
    collection: str,
    asset_key: str,
    name_key: str,
    search_period: int,
):
    logger.info(f"Connecting to STAC Catalog: {catalog}")
    stac_client = pystac_client.Client.open(url=catalog, ignore_conformance=True)

    feature = _get_random_feature(geojson_fp=geojson_file)
    feature_name = feature["properties"][name_key]
    logger.info(f"Feature selected: {feature_name}")

    scene_item = _get_scene(
        stac_client=stac_client,
        collection=collection,
        end_date=datetime.utcnow(),
        search_period=search_period,
        intersects=feature["geometry"],
    )

    logger.info("Creating map")
    scene_centroid = geometry.shape(scene_item.geometry).centroid
    m = _create_map(location=(scene_centroid.y, scene_centroid.x))

    logger.info(f"Adding scene {scene_item.id} to map")
    tile_layer = _create_tile_layer_from_item(item=scene_item, asset_key=asset_key)
    tile_layer.add_to(m)

    logger.info("Adding STAC info to feature")
    updated_feature = _add_stac_info_to_feature(
        feature=feature.copy(),
        item_id=scene_item.id,
        item_href=scene_item.self_href,
        asset_href=scene_item.assets[asset_key].href,
    )
    logger.info("Adding GeoJSON layer to map")
    marker_layer = _create_geojson_layer(
        geojson=dict(features=[updated_feature]), name="Marker"
    )
    marker_layer.add_to(m)

    folium.LayerControl().add_to(m)

    logger.info(f"Saving folium map to {output_file}")
    m.save(output_file)


if __name__ == "__main__":
    main()

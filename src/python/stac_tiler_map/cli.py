import click
import logging

from stac_tiler_map import create_stac_tiler_map
from settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


@click.command()
@click.argument(
    "geojson_file",
    default=settings.DEFAULT_GEOJSON,
    type=click.Path(exists=True, readable=True),
)
@click.argument("output_file", default=settings.DEFAULT_OUTPUT_FILE, type=click.Path())
@click.option(
    "--catalog",
    default=settings.DEFAULT_CATALOG,
    help="URL to a public STAC Catalog",
)
@click.option(
    "--collection",
    default=settings.DEFAULT_COLLECTION,
    help="STAC Collection ID to search",
)
@click.option(
    "--asset-key",
    default=settings.DEFAULT_ASSET_KEY,
    help="STAC asset key to add to map",
)
@click.option(
    "--name-key",
    default=settings.DEFAULT_NAME_KEY,
    help="Key in feature properties to show in map marker popup",
)
@click.option(
    "--search-period",
    default=settings.DEFAULT_SEARCH_PERIOD,
    help="Search period (in days)",
)
def main(
    geojson_file: str,
    output_file: str,
    catalog: str,
    collection: str,
    asset_key: str,
    name_key: str,
    search_period: int,
):
    m = create_stac_tiler_map(
        geojson_file=geojson_file,
        catalog=catalog,
        collection=collection,
        asset_key=asset_key,
        name_key=name_key,
        search_period=search_period,
    )

    logger.info(f"Saving folium map to {output_file}")
    m.save(outfile=output_file)


if __name__ == "__main__":
    main()

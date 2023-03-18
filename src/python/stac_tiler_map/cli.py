import logging
from typing import Union

import click
from schemas import CliInputs

from stac_tiler_map import create_stac_tiler_map

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

cli_inputs = CliInputs()


@click.command()
@click.argument(
    "geojson_path",
    default=cli_inputs.geojson,
    type=str,
)
@click.argument("output_file", default=cli_inputs.output_file, type=click.Path())
@click.option(
    "--catalog",
    default=cli_inputs.catalog,
    help="URL to a public STAC Catalog",
)
@click.option(
    "--collection",
    default=cli_inputs.collection,
    help="STAC Collection ID to search",
)
@click.option(
    "--asset-key",
    default=cli_inputs.asset_key,
    help="STAC asset key to add to map",
)
@click.option(
    "--search-period",
    default=cli_inputs.search_period,
    help="Search period (in days)",
)
def main(
    geojson_path: str,
    output_file: str,
    catalog: str,
    collection: str,
    asset_key: str,
    search_period: int,
):
    m = create_stac_tiler_map(
        geojson_path=geojson_path,
        catalog=catalog,
        collection=collection,
        asset_key=asset_key,
        search_period=search_period,
    )

    logger.info(f"Saving folium map to {output_file}")
    m.save(outfile=output_file)


if __name__ == "__main__":
    main()

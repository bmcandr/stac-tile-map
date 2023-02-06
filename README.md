# Display STAC COG with tiler on `folium` map

This is the result of a fun little weekend project inspired by @scottyhq's [`share-a-map`](https://github.com/scottyhq/share-a-map) repository.

The `create_map.py` script:

* selects a random National Park feature from `national-parks.geojson`
* searches [Element 84's EarthSearch STAC Catalog]("https://earth-search.aws.element84.com/v1") for the most recent Sentinel-2 L2A scenes that intersect the park location that have little no data or cloud coverage
* creates a tile layer using [Development Seed's](https://developmentseed.org/) public [COG tiler](https://cogeo.xyz/)
* generates an HTML file that displays the scene on an interactive map


I've also created [a GitHub Actions workflow](https://github.com/bmcandr/bmcandr.github.io/blob/main/.github/workflows/create_map.yml) to run this script every so often and commit the result to the repository, thereby periodically updating the map. Neat!

View the map here: https://bmcandr.github.io/map.html

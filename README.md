# STAC+COG Map

[![Docker CI/CD Pipeline](https://github.com/bmcandr/stac-tile-map/actions/workflows/ci-docker-lambda.yml/badge.svg)](https://github.com/bmcandr/stac-tile-map/actions/workflows/ci-docker-lambda.yml)

**TLDR;** [click here to view an interactive map displaying a recent Sentinel-2 image over a random National Park!](https://6ukssjutoemmbqd3x7diq2xmlm0rjrmn.lambda-url.us-east-1.on.aws/) Refresh for a new map.

## Overview

The code contained here:

* loads a GeoJSON file and randomly selects a feature
* searches [Element 84's EarthSearch STAC Catalog](https://earth-search.aws.element84.com/v1) for the most recent Sentinel-2 L2A scenes that intersect the selected geometry
* creates a `folium` map with a tile layer displaying a Cloud Optimized GeoTiff hosted in the [AWS Registry of Open Data](https://registry.opendata.aws/sentinel-2-l2a-cogs/) served via [Development Seed's](https://developmentseed.org/) public [COG tiler]

There is a CLI to generate a standalone HTML file and a FastAPI app for dynamically generating maps.

The FastAPI app is deployed to an AWS Lambda function using GitHub Actions.

## Setup

This repo uses [Poetry](https://python-poetry.org/) for dependency management. After cloning, run `poetry install` from the root directory to set up a virtual environment. Run `poetry shell` to activate the environment in your session.

Set `$PYTHONPATH` to the source path by changing directories into `src/python` and executing:

```bash
export PYTHONPATH=`pwd`
```

Change directories back to the root.

## Running the Thing

### Generating an HTML file

To generate an HTML file for local display, use the `click` CLI tool:

`python src/python/stac_tiler_map/cli.py`

Open the resulting `map.html` file with any web browser.

### Running a local server

There are several ways to run the FastAPI app locally: Python, `uvicorn`, Docker, and PEX.

* Python: `python src/python/api/main.py` (open `localhost:8080/`)
* `uvicorn`: `uvicorn src.python.api.main:app --reload --port 8080` (open `localhost:8080/`)
* Docker: `docker build -t stac-tiler-map . && docker run -p 8080:8080 stac-tiler-map`

[PEX](https://pex.readthedocs.io/en/v2.1.129/) is a little more involved. In short:

* [install Pants](https://www.pantsbuild.org/docs/installation)
* bootstrap Pants by running `pants -v`
* package the FastAPI app as a PEX with `pants --tag="pex" package ::`
* run the app from the PEX with `./dist/src.python.api/stac-tiler-map-api.pex api.main:app --port 8080`

### Deploying to AWS

I use a GitHub Actions workflow (`.github/workflows/ci-docker-lambda.yml`) to deploy the FastAPI app as a Docker-based AWS Lambda function. The GHA workflow builds an image from `Dockerfile.aws.lambda`, pushes the image to Elastic Container Registry, and updates the Lambda function with the new image. The link at the top of this is served by the Lambda function. Serverless is neat!

### Problems

It should be possible to deploy the FastAPI app to AWS Lambda as a PEX hosted in S3. The `.github/workflows/ci-pants-lambda.yml` file uses Pants to package the code in a Lambda-compliant PEX, uploads it to an S3 bucket, and updates the Lambda function. The app refuses to run, however, due to dependency issues (e.g., wheel tags don't match for `cryptography` library [`cp36` vs `cp39`]). Not sure how to fix this at the moment...

## Acknowledgements

This repo began as a weekend project inspired by @scottyhq's [`share-a-map`](https://github.com/scottyhq/share-a-map) repository. The first iteration used GitHub Actions to periodically generate a new map file via the CLI tool and commit the result to the repo which was then deployed to GitHub Pages. In this iteration, I use GitHub Actions to deploy to an AWS Lambda function backed by a Docker container hosted on AWS Elastic Container Registry. This is totally overkill, but it was a fun way to practice and learn.

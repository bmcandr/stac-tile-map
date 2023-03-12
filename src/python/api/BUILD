python_sources(dependencies=["//:root"])

pex_binary(
    name="stac-tiler-map-api",
    script="uvicorn",
    dependencies=[":api", "src/python/settings.py"],
    tags=["smoke-test"],
)

python_awslambda(
    name="stac-tiler-map-api-lambda",
    runtime="python3.9",
    handler="api.main:handler",
    tags=["deploy"],
)

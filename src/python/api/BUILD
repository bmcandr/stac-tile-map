python_sources(dependencies=["//:root"])

pex_binary(
    name="stac-tiler-map-api",
    script="uvicorn",
    platforms=[
        "current",
        # "linux-x86_64-cp-38-none"
    ],
    dependencies=[":api", "src/python/settings.py"],
)

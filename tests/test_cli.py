from click.testing import CliRunner

from stac_tiler_map.cli import main


def test_cli():
    runner = CliRunner()
    result = runner.invoke(main)

    assert result.exit_code == 0

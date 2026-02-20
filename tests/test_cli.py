from pathlib import Path

from typer.testing import CliRunner

from coldpy.cli import app


runner = CliRunner()
FIXTURE = Path(__file__).parent / "fixtures" / "sample_project"


def test_scan_command_writes_json_and_cache(tmp_path: Path) -> None:
    with runner.isolated_filesystem(temp_dir=tmp_path):
        json_output = Path("report.json")
        result = runner.invoke(
            app,
            ["scan", str(FIXTURE), "--json", str(json_output)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "ColdPy Scan Report" in result.stdout
        assert json_output.exists()


def test_top_requires_cache(tmp_path: Path) -> None:
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["top"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "Run `coldpy scan <path>` first" in result.stdout


def test_top_reads_cache_and_sorts(tmp_path: Path) -> None:
    with runner.isolated_filesystem(temp_dir=tmp_path):
        scan_result = runner.invoke(app, ["scan", str(FIXTURE)], catch_exceptions=False)
        assert scan_result.exit_code == 0

        top_result = runner.invoke(app, ["top", "2", "--sort", "memory", "--threshold-ms", "0", "--threshold-mb", "0"], catch_exceptions=False)
        assert top_result.exit_code == 0
        assert "ColdPy Top Imports" in top_result.stdout

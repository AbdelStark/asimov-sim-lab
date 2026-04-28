from typer.testing import CliRunner

from asimov_sim_lab.cli import app


def test_doctor_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "asimov-sim-lab scaffold ready" in result.stdout

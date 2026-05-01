from __future__ import annotations

from asimov_sim_lab.errors import LabError


def test_lab_error_string_includes_remediation() -> None:
    error = LabError("CODE", "message", "fix it")

    assert str(error) == "CODE: message Remediation: fix it"


def test_lab_error_string_without_remediation() -> None:
    error = LabError("CODE", "message")

    assert str(error) == "CODE: message"

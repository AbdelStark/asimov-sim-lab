"""Typed domain errors for Asimov Sim Lab.

Every public diagnostic carries a stable ``code`` (registered in
:mod:`asimov_sim_lab.error_registry`), a human ``message``, optional
``remediation`` guidance, and the CLI ``exit_code`` to surface.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LabError(Exception):
    """Recoverable command/domain error with a public, registered code."""

    code: str
    message: str
    remediation: str | None = None
    exit_code: int = 1

    def __str__(self) -> str:
        if self.remediation:
            return f"{self.code}: {self.message} Remediation: {self.remediation}"
        return f"{self.code}: {self.message}"

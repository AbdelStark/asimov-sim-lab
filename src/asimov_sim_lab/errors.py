"""Typed domain errors for Asimov Sim Lab."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LabError(Exception):
    """Recoverable command/domain error with a public code."""

    code: str
    message: str
    remediation: str | None = None
    exit_code: int = 1

    def __str__(self) -> str:
        if self.remediation:
            return f"{self.code}: {self.message} Remediation: {self.remediation}"
        return f"{self.code}: {self.message}"

from __future__ import annotations

import subprocess
import sys


def test_error_code_registry_matches_source() -> None:
    subprocess.run(
        [sys.executable, "scripts/check_error_registry.py", "--check"],
        check=True,
    )

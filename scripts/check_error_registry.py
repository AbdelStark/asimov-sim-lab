"""Verify the public error-code registry covers emitted diagnostic codes."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "src" / "asimov_sim_lab"
REGISTRY_PATH = ROOT / "docs" / "spec" / "ERROR-CODE-REGISTRY.md"

CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]*[A-Z0-9]$")
PREFIX_RE = re.compile(r"\b([A-Z][A-Z0-9]*_[A-Z0-9_]+):")
REGISTRY_ROW_RE = re.compile(r"^\|\s*`([A-Z][A-Z0-9_]+)`\s*\|")


def discover_source_codes(source_dir: Path = SOURCE_DIR) -> set[str]:
    """Extract diagnostic codes from Python source without executing the package."""
    codes: set[str] = set()
    for path in sorted(source_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = _DiagnosticCodeVisitor()
        visitor.visit(tree)
        codes.update(visitor.codes)
    return codes


def read_registry_codes(registry_path: Path = REGISTRY_PATH) -> set[str]:
    """Read backtick-wrapped codes from the registry's first table column."""
    try:
        lines = registry_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SystemExit(f"could not read registry: {registry_path}: {exc}") from exc

    codes: set[str] = set()
    duplicates: set[str] = set()
    for line in lines:
        match = REGISTRY_ROW_RE.match(line)
        if match is None:
            continue
        code = match.group(1)
        if code in codes:
            duplicates.add(code)
        codes.add(code)
    if duplicates:
        duplicated = ", ".join(sorted(duplicates))
        raise SystemExit(f"duplicate registry codes: {duplicated}")
    return codes


class _DiagnosticCodeVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.codes: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node.func)
        if name == "LabError" and node.args:
            self.codes.update(_codes_in_expr(node.args[0]))
        if name == "_path_check" and len(node.args) >= 3:
            self.codes.update(_codes_in_expr(node.args[2]))
        if name == "_viewer_issue" and node.args:
            self.codes.update(_codes_in_expr(node.args[0]))
        if name in {"DoctorCheck", "RuntimeSmokeResult", "ValidationIssue", "ViewerOpenResult"}:
            for keyword in node.keywords:
                if keyword.arg in {"code", "failure_code"}:
                    self.codes.update(_codes_in_expr(keyword.value))
        for keyword in node.keywords:
            if keyword.arg == "failure_code":
                self.codes.update(_codes_in_expr(keyword.value))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        target_names = {target.id for target in node.targets if isinstance(target, ast.Name)}
        if "STRICT_WARNING_CODES" in target_names:
            self.codes.update(_codes_in_expr(node.value))
        if "failure_code" in target_names:
            self.codes.update(_codes_in_expr(node.value))
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            self.codes.update(match.group(1) for match in PREFIX_RE.finditer(node.value))
            if node.value == "WARNING" or node.value.endswith("_WARNING"):
                self.codes.add(node.value)


def _call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _codes_in_expr(node: ast.AST) -> set[str]:
    codes: set[str] = set()
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Constant)
            and isinstance(child.value, str)
            and CODE_RE.fullmatch(child.value)
        ):
            codes.add(child.value)
    return codes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify registry coverage. Present for symmetry with other check scripts.",
    )
    args = parser.parse_args()
    _ = args.check

    source_codes = discover_source_codes()
    registry_codes = read_registry_codes()
    missing = sorted(source_codes - registry_codes)
    stale = sorted(registry_codes - source_codes)
    if missing or stale:
        for code in missing:
            print(f"missing registry code: {code}", file=sys.stderr)
        for code in stale:
            print(f"stale registry code: {code}", file=sys.stderr)
        raise SystemExit(1)
    print(f"error registry ok: {len(source_codes)} codes")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run the Windows-only PP02 formal-data inventory safety check."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.formal_data_inventory_service import (  # noqa: E402
    FormalDataInventoryError,
    FormalDataInventoryService,
)


class _InvalidArgumentsError(ValueError):
    """Internal marker for path-free CLI argument failures."""


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        raise _InvalidArgumentsError


class _SingleValueAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None) -> None:
        if getattr(namespace, self.dest, None) is not None:
            raise _InvalidArgumentsError
        setattr(namespace, self.dest, values)


def build_parser() -> argparse.ArgumentParser:
    parser = _PrivateArgumentParser(
        description=(
            "Create two verified local backups, then count only the four "
            "official PP02 portfolio ledger tables on a temporary copy."
        )
    )
    parser.add_argument(
        "--source",
        required=True,
        type=Path,
        action=_SingleValueAction,
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        action=_SingleValueAction,
    )
    parser.add_argument("--confirm-apps-closed", action="store_true")
    return parser


def _is_native_windows() -> bool:
    if os.name != "nt" or sys.platform != "win32":
        return False
    wsl_markers = ("WSL_INTEROP", "WSL_DISTRO_NAME")
    return not any(os.environ.get(marker) for marker in wsl_markers)


def _is_inside_git_repository(output_dir: Path) -> bool:
    candidate = output_dir.absolute()
    for parent in (candidate, *candidate.parents):
        marker = parent / ".git"
        if _is_git_marker(marker) or _is_bare_git_repository(parent):
            return True
    return False


def _is_git_marker(marker: Path) -> bool:
    if marker.is_symlink():
        return True
    if marker.is_dir():
        return (marker / "HEAD").is_file() and (
            (marker / "objects").is_dir() or (marker / "commondir").is_file()
        )
    if not marker.is_file():
        return False
    try:
        first_line = marker.read_text(encoding="utf-8", errors="strict").splitlines()[
            0
        ]
    except (OSError, UnicodeError, IndexError):
        return False
    return first_line.strip().lower().startswith("gitdir:")


def _is_bare_git_repository(path: Path) -> bool:
    return (
        (path / "HEAD").is_file()
        and (path / "objects").is_dir()
        and (path / "refs").is_dir()
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except _InvalidArgumentsError:
        print("invalid_arguments", file=sys.stderr)
        return 2
    if not _is_native_windows():
        print("wrong_environment", file=sys.stderr)
        return 2
    if not args.confirm_apps_closed:
        print("apps_not_confirmed_closed", file=sys.stderr)
        return 2
    if _is_inside_git_repository(args.output_dir):
        print("output_inside_git_repository", file=sys.stderr)
        return 2

    try:
        report = FormalDataInventoryService().run(
            source_path=args.source,
            output_dir=args.output_dir,
        )
    except FormalDataInventoryError as exc:
        print(exc.code, file=sys.stderr)
        return 2
    except Exception:
        print("unexpected_failure", file=sys.stderr)
        return 2

    print(report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

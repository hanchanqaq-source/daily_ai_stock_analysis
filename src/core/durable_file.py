"""Strict atomic publication primitives for full-data restore recovery state."""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Callable, Optional


MOVEFILE_REPLACE_EXISTING = 0x00000001
MOVEFILE_WRITE_THROUGH = 0x00000008
WindowsMoveFileEx = Callable[[str, str, int], object]


def _load_windows_move_file_ex() -> WindowsMoveFileEx:
    import ctypes

    move_file_ex = ctypes.WinDLL("kernel32", use_last_error=True).MoveFileExW
    move_file_ex.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
    move_file_ex.restype = ctypes.c_int
    return move_file_ex


def _windows_move_write_through(
    source: Path,
    destination: Path,
    move_file_ex: Optional[WindowsMoveFileEx],
) -> None:
    operation = move_file_ex or _load_windows_move_file_ex()
    flags = MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH
    if operation(str(source), str(destination), flags):
        return
    if move_file_ex is None:  # pragma: no cover - exercised on Windows
        import ctypes

        raise ctypes.WinError(ctypes.get_last_error())
    raise OSError("MoveFileExW durable publication failed")


def _fsync_directory_strict(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def durable_replace(
    staged_path: Path,
    destination: Path,
    *,
    platform_name: Optional[str] = None,
    windows_move_file_ex: Optional[WindowsMoveFileEx] = None,
) -> None:
    """Publish an already-fsynced file with platform durability guarantees."""
    platform = platform_name or os.name
    if platform == "nt":
        _windows_move_write_through(
            staged_path,
            destination,
            windows_move_file_ex,
        )
        return
    os.replace(staged_path, destination)
    _fsync_directory_strict(destination.parent)


def durable_unlink(
    path: Path,
    *,
    platform_name: Optional[str] = None,
    windows_move_file_ex: Optional[WindowsMoveFileEx] = None,
) -> None:
    """Durably make a recovery path undiscoverable, tolerating absence."""
    if not path.exists():
        return
    platform = platform_name or os.name
    if platform == "nt":
        tombstone = path.parent / (
            f".{path.name}.cleared-{os.getpid()}-{secrets.token_hex(8)}"
        )
        _windows_move_write_through(path, tombstone, windows_move_file_ex)
        tombstone.unlink()
        return
    path.unlink()
    _fsync_directory_strict(path.parent)

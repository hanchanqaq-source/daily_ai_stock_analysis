"""Strict durability primitives used only by full-data restore state."""

from __future__ import annotations

import os

import pytest

from src.core import durable_file


def test_windows_durable_replace_uses_replace_and_write_through(tmp_path) -> None:
    staged = tmp_path / "staged.tmp"
    destination = tmp_path / "journal.json"
    staged.write_bytes(b"new")
    destination.write_bytes(b"old")
    calls = []

    def move_file_ex(source, target, flags):
        calls.append((source, target, flags))
        os.replace(source, target)
        return True

    durable_file.durable_replace(
        staged,
        destination,
        platform_name="nt",
        windows_move_file_ex=move_file_ex,
    )

    assert destination.read_bytes() == b"new"
    assert calls == [
        (
            str(staged),
            str(destination),
            durable_file.MOVEFILE_REPLACE_EXISTING
            | durable_file.MOVEFILE_WRITE_THROUGH,
        )
    ]


def test_windows_durable_replace_failure_is_not_silenced(tmp_path) -> None:
    staged = tmp_path / "staged.tmp"
    destination = tmp_path / "journal.json"
    staged.write_bytes(b"new")
    destination.write_bytes(b"old")

    with pytest.raises(OSError, match="MoveFileExW"):
        durable_file.durable_replace(
            staged,
            destination,
            platform_name="nt",
            windows_move_file_ex=lambda *_args: False,
        )

    assert staged.read_bytes() == b"new"
    assert destination.read_bytes() == b"old"


def test_windows_durable_unlink_publishes_write_through_tombstone(tmp_path) -> None:
    target = tmp_path / "journal.json"
    target.write_bytes(b"pending")
    calls = []

    def move_file_ex(source, destination, flags):
        calls.append((source, destination, flags))
        os.replace(source, destination)
        return True

    durable_file.durable_unlink(
        target,
        platform_name="nt",
        windows_move_file_ex=move_file_ex,
    )

    assert not target.exists()
    assert len(calls) == 1
    assert calls[0][0] == str(target)
    assert calls[0][2] == (
        durable_file.MOVEFILE_REPLACE_EXISTING
        | durable_file.MOVEFILE_WRITE_THROUGH
    )
    assert not list(tmp_path.glob(".journal.json.cleared-*"))


def test_posix_directory_fsync_failure_propagates(tmp_path, monkeypatch) -> None:
    staged = tmp_path / "staged.tmp"
    destination = tmp_path / "journal.json"
    staged.write_bytes(b"new")
    destination.write_bytes(b"old")

    def fail_directory_fsync(_directory):
        raise OSError("injected directory fsync failure")

    monkeypatch.setattr(durable_file, "_fsync_directory_strict", fail_directory_fsync)

    with pytest.raises(OSError, match="directory fsync failure"):
        durable_file.durable_replace(
            staged,
            destination,
            platform_name="posix",
        )

    assert destination.read_bytes() == b"new"

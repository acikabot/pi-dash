"""Reading and writing the files the bots keep: logs, prompts, small JSON configs."""

from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path

from pidash.services.systemd import run

logger = logging.getLogger(__name__)


def tail(path: Path | str, lines: int = 200) -> str:
    """The last lines of a file, or "" when it isn't there yet."""
    path = Path(path)
    if not path.is_file():
        return ""
    rc, out, _err = run(["tail", "-n", str(max(1, min(lines, 5000))), str(path)], timeout=10)
    return out if rc == 0 else ""


def last_activity(path: Path | str) -> str | None:
    """The newest timestamp in a log, for "last seen" on a card."""
    for line in reversed(tail(path, 40).splitlines()):
        parts = line.split()
        if len(parts) >= 2 and parts[0].count("-") == 2 and parts[1].count(":") == 2:
            return f"{parts[0]} {parts[1][:8]}"
    return None


def size_of(path: Path | str) -> int:
    path = Path(path)
    return path.stat().st_size if path.is_file() else 0


def clear(path: Path | str) -> None:
    """Empty a log without deleting it, so whatever is writing keeps its handle."""
    path = Path(path)
    if path.is_file():
        with path.open("w"):
            pass


def read_text(path: Path | str, default: str = "") -> str:
    path = Path(path)
    return path.read_text(encoding="utf-8") if path.is_file() else default


#: Files written for the bots belong to a shared group, so both sides can edit them.
SHARED_MODE = 0o660


def _keep_shared(path: Path, previous: os.stat_result | None) -> None:
    """Leave a file the bots' group can still read and write.

    Writing replaces the file, so without this a prompt saved from the dashboard would
    come back owned by the dashboard alone — and the person who owns the bots could no
    longer edit it by hand.
    """
    if previous is not None:
        try:
            os.chown(path, -1, previous.st_gid)
        except OSError:
            pass
    try:
        os.chmod(path, SHARED_MODE)
    except OSError:
        pass


def write_text(path: Path | str, text: str, *, backup: bool = True) -> None:
    """Write a file, keeping one .bak copy.

    Replacing the file in one step is the safer way, but it needs permission to create a
    file in the folder — and the dashboard is deliberately allowed to write a bot's
    config without being allowed to add files next to its code. When that is the case it
    writes in place instead, which is why the .bak copy is taken first.
    """
    path = Path(path)
    previous = path.stat() if path.is_file() else None
    if backup and previous is not None:
        backup_path = path.with_suffix(path.suffix + ".bak")
        try:
            shutil.copyfile(path, backup_path)
            _keep_shared(backup_path, previous)
        except OSError as error:  # a backup is nice to have; the save itself matters more
            logger.warning("Could not keep a backup of %s: %s", path, error)

    if os.access(path.parent, os.W_OK):
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)
    else:
        path.write_text(text, encoding="utf-8")
    _keep_shared(path, previous)


def read_json(path: Path | str, default=None):
    try:
        return json.loads(read_text(path, "")) if Path(path).is_file() else default
    except json.JSONDecodeError:
        return default


def write_json(path: Path | str, data) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def human_size(number: int) -> str:
    step = float(number)
    for unit in ("B", "KB", "MB", "GB"):
        if step < 1024 or unit == "GB":
            return f"{step:.0f} {unit}" if unit == "B" else f"{step:.1f} {unit}"
        step /= 1024
    return f"{step:.1f} GB"

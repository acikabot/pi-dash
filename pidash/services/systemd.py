"""Everything that talks to systemd.

This is the only place the dashboard runs a privileged command, so the account it runs
as needs exactly one narrow sudo rule (see deploy/sudoers.pidash).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime

SYSTEMCTL = shutil.which("systemctl") or "/bin/systemctl"
ACTIONS = ("start", "stop", "restart")


@dataclass(frozen=True)
class UnitState:
    active: str = "unknown"
    sub: str = ""
    enabled: str = ""
    since: str = ""
    memory_bytes: int | None = None
    result: str = ""

    @property
    def is_active(self) -> bool:
        return self.active == "active"

    @property
    def is_failed(self) -> bool:
        return self.active == "failed" or self.result not in ("", "success")

    @property
    def is_busy(self) -> bool:
        return self.active == "activating" or self.sub == "start"


def run(argv: list[str], timeout: int = 15) -> tuple[int, str, str]:
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return done.returncode, done.stdout.strip(), done.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -1, "", f"Command not found: {argv[0]}"


PROPERTIES = "ActiveState,SubState,UnitFileState,ActiveEnterTimestamp,MemoryCurrent,Result"


def _parse(block: str) -> UnitState:
    props = dict(line.split("=", 1) for line in block.splitlines() if "=" in line)
    memory = props.get("MemoryCurrent", "")
    return UnitState(
        active=props.get("ActiveState", "unknown"),
        sub=props.get("SubState", ""),
        enabled=props.get("UnitFileState", ""),
        since=props.get("ActiveEnterTimestamp", ""),
        memory_bytes=int(memory) if memory.isdigit() else None,
        result=props.get("Result", ""),
    )


def unit_states(units: list[str]) -> dict[str, UnitState]:
    """Ask about every unit in one call — a subprocess each would be slow on a Pi."""
    units = [unit for unit in units if unit]
    if not units:
        return {}
    rc, out, _err = run([SYSTEMCTL, "show", *units, "--no-pager", f"--property={PROPERTIES}"])
    if rc != 0:
        return {unit: UnitState() for unit in units}
    blocks = [block for block in out.split("\n\n") if block.strip()]
    # systemd answers in the order asked, one block per unit.
    return {unit: _parse(block) for unit, block in zip(units, blocks, strict=False)}


def unit_state(unit: str) -> UnitState:
    return unit_states([unit]).get(unit, UnitState())


def control(unit: str, action: str, timeout: int = 30) -> tuple[bool, str]:
    """start / stop / restart a unit. Returns (ok, message)."""
    if action not in ACTIONS:
        return False, f"Unknown action {action!r}"
    rc, _out, err = run(["sudo", "-n", SYSTEMCTL, action, unit], timeout=timeout)
    return rc == 0, err or ("" if rc == 0 else "systemctl failed")


def start_unit(unit: str, timeout: int = 30) -> tuple[bool, str]:
    return control(unit, "start", timeout)


def from_usec(value) -> datetime | None:
    """systemd reports timer times as microseconds since the epoch, or 0 for never."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(number / 1_000_000, tz=UTC) if number > 0 else None


def human_delta(delta) -> str:
    """A rough "3d 4h" / "2h 15m" / "45s", for "runs in" and "ran ago"."""
    seconds = int(abs(delta.total_seconds()))
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, seconds = divmod(rest, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m" if minutes else f"{seconds}s"


def power(action: str, timeout: int = 20) -> tuple[bool, str]:
    """Reboot or power off the machine. These are verbs, not units."""
    if action not in ("reboot", "poweroff"):
        return False, f"Unknown action {action!r}"
    rc, _out, err = run(["sudo", "-n", SYSTEMCTL, action], timeout=timeout)
    return rc == 0, err or ("" if rc == 0 else "systemctl failed")


def timers() -> list[dict]:
    rc, out, _err = run([SYSTEMCTL, "list-timers", "--all", "--no-pager", "--output=json"])
    if rc != 0 or not out:
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return []


def timer_rows() -> dict[str, dict]:
    """Timer facts keyed by unit: when it runs next, when it last ran, and how long that is.

    The JSON from systemd carries raw timestamps (its own "left" and "passed" fields are
    not the deltas they look like), so the waiting times are worked out here.
    """
    moment = now()
    rows = {}
    for row in timers():
        unit = row.get("unit", "")
        if not unit:
            continue
        next_at, last_at = from_usec(row.get("next")), from_usec(row.get("last"))
        rows[unit] = {
            "unit": unit,
            "next_at": next_at,
            "last_at": last_at,
            "in": human_delta(next_at - moment) if next_at else "",
            "ago": human_delta(moment - last_at) if last_at else "",
        }
    return rows


def uptime_since(state: UnitState) -> datetime | None:
    """When the unit went active, as a datetime (systemd prints a wordy timestamp)."""
    if not state.since or state.since in ("n/a", "0"):
        return None
    for pattern in ("%a %Y-%m-%d %H:%M:%S %Z", "%a %Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(state.since, pattern)
        except ValueError:
            continue
        return parsed if parsed.tzinfo else parsed.astimezone()
    return None


def is_healthy(url: str, timeout: int = 4) -> bool | None:
    """True/False for a health URL, None when there is nothing to check."""
    if not url:
        return None
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - fixed config
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def now() -> datetime:
    return datetime.now(UTC)

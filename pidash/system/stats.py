"""How the Pi itself is doing."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import psutil

THERMAL = Path("/sys/class/thermal/thermal_zone0/temp")
REBOOT_REQUIRED = Path("/var/run/reboot-required")


@dataclass(frozen=True)
class Tile:
    label: str
    value: str
    detail: str
    percent: int | None = None
    tone: str = "primary"


def cpu_temperature() -> float | None:
    try:
        return round(int(THERMAL.read_text().strip()) / 1000, 1)
    except (OSError, ValueError):
        return None


def uptime() -> str:
    booted = datetime.fromtimestamp(psutil.boot_time(), tz=UTC)
    delta = datetime.now(UTC) - booted
    days, rest = divmod(int(delta.total_seconds()), 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    return f"{days}d {hours}h {minutes}m" if days else f"{hours}h {minutes}m"


def booted_at() -> datetime:
    return datetime.fromtimestamp(psutil.boot_time(), tz=UTC)


def _tone(percent: float, warn: int, bad: int) -> str:
    if percent >= bad:
        return "danger"
    return "warning" if percent >= warn else "primary"


def tiles() -> list[Tile]:
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    load = os.getloadavg()
    temperature = cpu_temperature()
    cpu = psutil.cpu_percent(interval=0.3)

    result = [
        Tile("CPU", f"{cpu:.1f}%", f"load {load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}",
             int(cpu), _tone(cpu, 70, 90)),
    ]  # fmt: skip
    if temperature is not None:
        result.append(
            Tile("Temperature", f"{temperature:.0f}°C",
                 "normal" if temperature < 70 else "warm",
                 int(min(temperature, 100)), _tone(temperature, 70, 80))
        )  # fmt: skip
    result += [
        Tile("Memory", f"{memory.percent:.1f}%",
             f"{memory.used / 1024**3:.1f} of {memory.total / 1024**3:.2f} GB",
             int(memory.percent), _tone(memory.percent, 80, 92)),
        Tile("Disk", f"{disk.percent:.1f}%",
             f"{disk.used / 1024**3:.0f} of {disk.total / 1024**3:.0f} GB",
             int(disk.percent), _tone(disk.percent, 80, 92)),
        Tile("Uptime", uptime(), f"since {booted_at().astimezone():%d %b %H:%M}"),
    ]  # fmt: skip
    return result


def reboot_required() -> bool:
    return REBOOT_REQUIRED.exists()

"""The services the dashboard manages, read from config/services.py."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

from django.conf import settings

KINDS = ("resident", "scheduled", "app")


@dataclass(frozen=True)
class Run:
    label: str
    mode: str


@dataclass(frozen=True)
class Prompt:
    id: str
    label: str
    desc: str
    vars: tuple[str, ...]


@dataclass(frozen=True)
class Service:
    id: str
    name: str
    blurb: str
    kind: str
    unit: str
    timer: str | None
    dir: str
    log: str
    runs: tuple[Run, ...] = ()
    config: str | None = None
    prompts: tuple[Prompt, ...] = ()
    health: str | None = None
    url: str | None = None
    #: Sends e-mail, so it appears on the recipients page.
    email: bool = False

    @property
    def service_unit(self) -> str:
        return f"{self.unit}.service"

    @property
    def timer_unit(self) -> str | None:
        return f"{self.timer}.timer" if self.timer else None

    @property
    def control_unit(self) -> str:
        """What start/stop/restart act on: the timer for scheduled work."""
        return self.timer_unit if self.kind == "scheduled" and self.timer else self.service_unit

    def run_unit(self, mode: str) -> str:
        """A manual run always goes through systemd, as its own unit."""
        return f"{self.unit}@{mode}.service" if mode else self.service_unit

    @property
    def log_path(self) -> Path:
        return Path(self.dir) / self.log if not self.log.startswith("/") else Path(self.log)

    @property
    def prompts_dir(self) -> Path:
        return Path(self.dir) / "prompts"

    def prompt(self, prompt_id: str) -> Prompt | None:
        return next((p for p in self.prompts if p.id == prompt_id), None)

    def has_run(self, mode: str) -> bool:
        return any(run.mode == mode for run in self.runs)


def _build(entry: dict[str, Any]) -> Service:
    return Service(
        id=entry["id"],
        name=entry["name"],
        blurb=entry.get("blurb", ""),
        kind=entry["kind"],
        unit=entry["unit"],
        timer=entry.get("timer"),
        dir=entry["dir"],
        log=entry.get("log", ""),
        runs=tuple(Run(r["label"], r["mode"]) for r in entry.get("runs", [])),
        config=entry.get("config"),
        prompts=tuple(
            Prompt(p["id"], p["label"], p.get("desc", ""), tuple(p.get("vars", [])))
            for p in entry.get("prompts", [])
        ),
        health=entry.get("health"),
        url=entry.get("url"),
        email=entry.get("email", False),
    )


def services() -> list[Service]:
    """Every configured service, in the order they are listed."""
    module = import_module(settings.PIDASH_SERVICES_MODULE)
    return [_build(entry) for entry in module.SERVICES]


def get_service(service_id: str) -> Service | None:
    return next((s for s in services() if s.id == service_id), None)


def services_with(attribute: str) -> list[Service]:
    """Services that have prompts, a config file, a log… — used to build the pages."""
    return [s for s in services() if getattr(s, attribute)]

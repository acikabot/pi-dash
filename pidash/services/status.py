"""What a service is doing right now: state, health, memory, uptime, next run."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from pidash.core.files import human_size, last_activity, size_of
from pidash.services import systemd
from pidash.services.catalog import Service, services


@dataclass(frozen=True)
class Status:
    service: Service
    state: systemd.UnitState
    timer_state: systemd.UnitState | None
    healthy: bool | None
    label: str
    tone: str  # ok | bad | idle | busy
    memory: str
    uptime: str
    next_run: str
    last_activity: str | None
    log_size: str

    #: Bootstrap classes for the badge and the dot, by tone.
    BADGES = {"ok": "text-bg-success", "bad": "text-bg-danger",
              "idle": "text-bg-secondary", "busy": "text-bg-warning"}  # fmt: skip

    @property
    def badge(self) -> str:
        return self.BADGES.get(self.tone, "text-bg-secondary")

    @property
    def dot(self) -> str:
        return f"dot dot-{self.tone}"

    @property
    def is_problem(self) -> bool:
        return self.tone == "bad"

    @property
    def can_stop(self) -> bool:
        unit = self.timer_state if self.service.kind == "scheduled" else self.state
        return bool(unit and unit.is_active)


def _describe(service: Service, state, timer_state, healthy) -> tuple[str, str]:
    """The badge text and its colour."""
    if state.is_busy:
        return "Working", "busy"

    if service.kind == "scheduled":
        if state.is_failed:
            return "Last run failed", "bad"
        if timer_state and timer_state.is_active:
            return "Scheduled", "ok"
        return "Timer off", "idle"

    if state.is_active:
        if healthy is False:
            return "Not answering", "bad"
        return "Running", "ok"
    if state.active == "failed":
        return "Failed", "bad"
    return "Stopped", "idle"


def _uptime(state) -> str:
    started = systemd.uptime_since(state)
    if started is None or not state.is_active:
        return ""
    delta: timedelta = systemd.now() - started
    days, rest = divmod(int(delta.total_seconds()), 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return f"{days}d {hours}h"
    return f"{hours}h {minutes}m" if hours else f"{minutes}m"


def status_for(
    service: Service,
    timers: dict[str, str] | None = None,
    states: dict[str, systemd.UnitState] | None = None,
) -> Status:
    states = (
        states
        if states is not None
        else systemd.unit_states([service.service_unit, service.timer_unit or ""])
    )
    state = states.get(service.service_unit) or systemd.UnitState()
    timer_state = states.get(service.timer_unit) if service.timer_unit else None
    healthy = systemd.is_healthy(service.health) if service.health and state.is_active else None
    label, tone = _describe(service, state, timer_state, healthy)
    next_run = ""
    if service.timer_unit and timers is not None:
        next_run = timers.get(service.timer_unit, "")
    return Status(
        service=service,
        state=state,
        timer_state=timer_state,
        healthy=healthy,
        label=label,
        tone=tone,
        memory=human_size(state.memory_bytes) if state.memory_bytes else "",
        uptime=_uptime(state),
        next_run=next_run,
        last_activity=last_activity(service.log_path) if service.log else None,
        log_size=human_size(size_of(service.log_path)) if service.log else "",
    )


def next_runs() -> dict[str, str]:
    """How long until each timer fires, keyed by unit name."""
    return {unit: row["in"] for unit, row in systemd.timer_rows().items()}


def all_statuses() -> list[Status]:
    everything = services()
    units = [s.service_unit for s in everything] + [s.timer_unit for s in everything if s.timer]
    states = systemd.unit_states(units)
    timers = next_runs()
    return [status_for(service, timers, states) for service in everything]

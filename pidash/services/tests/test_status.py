"""The badge on a card says what is actually going on."""

import pytest

from pidash.services import systemd
from pidash.services.catalog import get_service
from pidash.services.status import all_statuses, status_for


def states(**kwargs):
    """A unit state dict for the service and, when asked, its timer."""
    return {unit: systemd.UnitState(**props) for unit, props in kwargs.items()}


@pytest.mark.parametrize(
    "service_id, unit_props, label, tone",
    [
        ("always", {"active": "active", "sub": "running"}, "Running", "ok"),
        ("always", {"active": "inactive"}, "Stopped", "idle"),
        ("always", {"active": "failed"}, "Failed", "bad"),
        ("always", {"active": "activating", "sub": "start"}, "Working", "busy"),
    ],
)
def test_a_resident_service_reports_its_state(service_id, unit_props, label, tone, fake_systemd):
    service = get_service(service_id)
    status = status_for(service, {}, states(**{service.service_unit: unit_props}))
    assert (status.label, status.tone) == (label, tone)


def test_a_scheduled_service_follows_its_timer(fake_systemd):
    service = get_service("timed")
    on = states(**{service.service_unit: {"active": "inactive"},
                   service.timer_unit: {"active": "active"}})  # fmt: skip
    off = states(**{service.service_unit: {"active": "inactive"},
                    service.timer_unit: {"active": "inactive"}})  # fmt: skip
    assert status_for(service, {}, on).label == "Scheduled"
    assert status_for(service, {}, off).label == "Timer off"


def test_a_failed_last_run_shows_up(fake_systemd):
    service = get_service("timed")
    broken = states(**{service.service_unit: {"active": "failed", "result": "exit-code"},
                       service.timer_unit: {"active": "active"}})  # fmt: skip
    status = status_for(service, {}, broken)
    assert (status.label, status.is_problem) == ("Last run failed", True)


def test_a_web_app_that_does_not_answer_is_a_problem(fake_systemd, monkeypatch):
    monkeypatch.setattr(systemd, "is_healthy", lambda url, timeout=4: False)
    service = get_service("web")
    status = status_for(service, {}, states(**{service.service_unit: {"active": "active"}}))
    assert (status.label, status.is_problem) == ("Not answering", True)


def test_cards_carry_uptime_memory_and_last_activity(fake_systemd):
    statuses = {s.service.id: s for s in all_statuses()}
    assert statuses["always"].memory == "50.0 MB"
    assert statuses["always"].uptime  # started at a known time, so it has one
    assert statuses["always"].last_activity == "2026-09-20 10:01:00"

"""Failure alerts: one message per failure, and one when it comes back."""

import pytest
from django.core.management import call_command

from pidash.alerts import notify
from pidash.alerts.models import ServiceAlert
from pidash.services import status as status_module

pytestmark = pytest.mark.django_db


@pytest.fixture
def sent(monkeypatch):
    messages = []
    monkeypatch.setattr(
        notify, "send", lambda title, message, **kwargs: messages.append(title) or True
    )
    monkeypatch.setattr(
        "pidash.alerts.management.commands.check_services.send",
        lambda title, message, **kwargs: messages.append(title) or True,
    )
    return messages


def pretend(monkeypatch, *, broken):
    """Make every service look fine, or make one of them look broken."""
    real = status_module.all_statuses

    def fake():
        statuses = []
        for status in real():
            if broken and status.service.id == "always":
                statuses.append(
                    status_module.Status(**{**status.__dict__, "label": "Failed", "tone": "bad"})
                )
            else:
                statuses.append(status)
        return statuses

    monkeypatch.setattr("pidash.alerts.management.commands.check_services.all_statuses", fake)


def test_nothing_is_sent_while_everything_is_fine(monkeypatch, sent, fake_systemd):
    pretend(monkeypatch, broken=False)
    call_command("check_services")
    assert sent == [] and ServiceAlert.objects.count() == 0


def test_a_failure_is_reported_once(monkeypatch, sent, fake_systemd):
    pretend(monkeypatch, broken=True)
    call_command("check_services")
    call_command("check_services")  # still broken: no second message
    assert len(sent) == 1
    assert ServiceAlert.objects.get().service_id == "always"


def test_recovery_is_reported_and_clears_the_alert(monkeypatch, sent, fake_systemd):
    pretend(monkeypatch, broken=True)
    call_command("check_services")
    pretend(monkeypatch, broken=False)
    call_command("check_services")
    assert len(sent) == 2 and "back to normal" in sent[1]
    assert ServiceAlert.objects.count() == 0

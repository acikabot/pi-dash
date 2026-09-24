"""The buttons on the cards, and who may press them."""

from django.urls import reverse

from pidash.services.systemd import SYSTEMCTL


def test_pages_need_a_sign_in(client):
    response = client.get(reverse("services:page"))
    assert response.status_code == 302
    assert reverse("core:login") in response["Location"]


def test_the_page_lists_every_service(client_in, fake_systemd):
    body = client_in.get(reverse("services:page")).content.decode()
    assert "Always Bot" in body and "Timed Bot" in body and "Web App" in body


def test_restart_acts_on_the_right_unit(client_in, fake_systemd):
    client_in.post(reverse("services:control", args=["timed"]), {"action": "restart"})
    # A scheduled service is restarted through its timer, not its service unit.
    assert ["sudo", "-n", SYSTEMCTL, "restart", "timed-bot.timer"] in fake_systemd


def test_an_unknown_action_is_refused(client_in, fake_systemd):
    response = client_in.post(reverse("services:control", args=["always"]), {"action": "destroy"})
    assert response.status_code == 302
    assert not any("destroy" in " ".join(call) for call in fake_systemd)


def test_a_manual_run_starts_its_own_unit(client_in, fake_systemd):
    client_in.post(reverse("services:run", args=["always"]), {"mode": "test"})
    assert ["sudo", "-n", SYSTEMCTL, "start", "always-bot@test.service"] in fake_systemd


def test_a_run_that_is_not_offered_is_refused(client_in, fake_systemd):
    client_in.post(reverse("services:run", args=["always"]), {"mode": "rm-rf"})
    assert not any("rm-rf" in " ".join(call) for call in fake_systemd)


def test_the_health_chip_counts_problems(client_in, fake_systemd):
    assert "All good" in client_in.get(reverse("services:health")).content.decode()

"""The system page: figures, bulk actions and power."""

from django.urls import reverse

from pidash.services.systemd import SYSTEMCTL


def test_the_tiles_describe_the_pi(client_in):
    body = client_in.get(reverse("system:page")).content.decode()
    assert "CPU" in body and "Memory" in body and "Uptime" in body


def test_restart_all_touches_every_service(client_in, fake_systemd):
    client_in.post(reverse("system:bulk"), {"action": "restart"})
    restarted = {call[-1] for call in fake_systemd if "restart" in call}
    assert restarted == {"always-bot.service", "timed-bot.timer", "web-app.service"}


def test_clearing_all_logs_empties_them(client_in, fake_systemd):
    from pidash.services.catalog import services

    client_in.post(reverse("system:clear_logs"))
    assert all(s.log_path.read_text() == "" for s in services() if s.log_path.is_file())


def test_reboot_goes_through_systemd(client_in, fake_systemd):
    client_in.post(reverse("system:power"), {"action": "reboot"})
    assert ["sudo", "-n", SYSTEMCTL, "reboot"] in fake_systemd


def test_an_unknown_power_action_does_nothing(client_in, fake_systemd):
    client_in.post(reverse("system:power"), {"action": "explode"})
    assert not any("explode" in " ".join(call) for call in fake_systemd)


def test_the_schedule_page_renders(client_in, fake_systemd):
    assert client_in.get(reverse("system:schedule")).status_code == 200

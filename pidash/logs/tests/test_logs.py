"""Reading and clearing logs."""

from django.urls import reverse

from pidash.services.catalog import get_service


def test_the_log_is_shown(client_in, fake_systemd):
    body = client_in.get(reverse("logs:page"), {"service": "always"}).content.decode()
    assert "did a thing" in body


def test_the_filter_keeps_only_matching_lines(client_in, fake_systemd):
    page = client_in.get(reverse("logs:page"), {"service": "always", "find": "started"})
    body = page.content.decode()
    assert "started" in body and "did a thing" not in body


def test_an_unknown_service_is_a_404(client_in, fake_systemd):
    assert client_in.get(reverse("logs:page"), {"service": "nope"}).status_code == 404


def test_clearing_empties_the_file(client_in, fake_systemd):
    client_in.post(reverse("logs:clear", args=["always"]))
    assert get_service("always").log_path.read_text() == ""

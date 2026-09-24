"""Recipients live in one shared file, not in the bots' .env files."""

from django.urls import reverse

from pidash.recipients import store


def test_only_bots_that_send_email_are_listed(client_in):
    body = client_in.get(reverse("recipients:page")).content.decode()
    assert "Always Bot" in body and "Timed Bot" not in body


def test_saving_writes_the_shared_file(client_in):
    client_in.post(reverse("recipients:save", args=["always"]), {"addresses": "a@b.com, c@d.com"})
    assert store.get("always") == "a@b.com, c@d.com"
    assert store.path().is_file()


def test_a_service_that_sends_no_email_is_refused(client_in):
    response = client_in.post(reverse("recipients:save", args=["timed"]), {"addresses": "x@y.com"})
    assert response.status_code == 404

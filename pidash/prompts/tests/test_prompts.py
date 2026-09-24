"""Editing prompts: saved, validated, and restorable."""

from django.urls import reverse

from pidash.services.catalog import get_service


def prompt_file(name="style.txt"):
    return get_service("always").prompts_dir / name


def test_the_page_shows_the_text_on_disk(client_in):
    body = client_in.get(reverse("prompts:page")).content.decode()
    assert "Write nicely." in body


def test_a_prompt_with_no_file_yet_falls_back_to_the_default(client_in):
    body = client_in.get(reverse("prompts:page")).content.decode()
    assert "Summarise {text}." in body  # digest.txt does not exist, only its default
    assert "using the default" in body


def test_saving_writes_the_file_and_keeps_a_backup(client_in):
    before = prompt_file().read_text()
    response = client_in.post(
        reverse("prompts:save", args=["always", "style"]), {"text": "Write briefly."}
    )
    assert response.status_code == 302
    assert prompt_file().read_text() == "Write briefly."
    assert prompt_file("style.txt.bak").read_text() == before


def test_a_prompt_that_drops_its_placeholder_is_refused(client_in):
    target = prompt_file("digest.txt")
    client_in.post(reverse("prompts:save", args=["always", "digest"]), {"text": "Summarise it."})
    assert not target.exists()  # nothing was written


def test_an_empty_prompt_is_refused(client_in):
    client_in.post(reverse("prompts:save", args=["always", "style"]), {"text": "   "})
    assert prompt_file().read_text() != "   "


def test_reset_puts_the_original_back(client_in):
    prompt_file().write_text("something else")
    client_in.post(reverse("prompts:reset", args=["always", "style"]))
    assert prompt_file().read_text() == "Write plainly.\n"


def test_an_unknown_prompt_is_a_404(client_in):
    response = client_in.post(reverse("prompts:save", args=["always", "nope"]), {"text": "x"})
    assert response.status_code == 404

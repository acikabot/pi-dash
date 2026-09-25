"""The documentation pages, and who may read the private one."""

import pytest
from django.test import Client
from django.urls import reverse

from pidash.docs import documents as docs


@pytest.fixture
def project(settings, tmp_path):
    """A small project folder with one public and one private document."""
    settings.BASE_DIR = tmp_path
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(
        "# Pi control\n\nWhat this is.\n\n## Setting it up\n\nSee [the notes](docs/_notes.md).\n"
    )
    (tmp_path / "docs" / "_notes.md").write_text("# Private notes\n\nOnly for owners.\n")
    docs._cache.clear()
    return tmp_path


def test_both_documents_are_found(project):
    found = docs.documents()
    assert set(found) == {"guide", "notes"}
    assert found["guide"].title == "Pi control"
    assert found["notes"].owner_only is True


def test_the_index_lists_them_for_an_owner(client_in, project):
    body = client_in.get(reverse("docs:index")).content.decode()
    assert "Pi control" in body and "Private notes" in body


def test_markdown_becomes_html_with_a_contents_list(client_in, project):
    body = client_in.get(reverse("docs:page", args=["guide"])).content.decode()
    assert 'id="setting-it-up"' in body  # headings get anchors
    assert reverse("docs:page", args=["notes"]) in body  # links between docs are rewritten


def test_a_private_document_is_hidden_from_other_accounts(helper_client, project):
    assert "Private notes" not in helper_client.get(reverse("docs:index")).content.decode()
    assert helper_client.get(reverse("docs:page", args=["notes"])).status_code == 404


def test_an_unknown_document_is_a_404(client_in, project):
    assert client_in.get(reverse("docs:page", args=["nope"])).status_code == 404


def test_the_documents_need_a_sign_in(project):
    response = Client().get(reverse("docs:index"))
    assert response.status_code == 302 and reverse("core:login") in response["Location"]


def test_they_are_linked_from_the_settings_page(client_in, project, fake_systemd):
    body = client_in.get(reverse("recipients:page")).content.decode()
    assert "Documentation" in body and reverse("docs:page", args=["guide"]) in body


def test_pictures_are_served_and_outside_ones_become_labels(client_in, project):
    (project / "docs" / "images").mkdir()
    (project / "docs" / "images" / "home.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (project / "README.md").write_text(
        "# Pi control\n\n![Home page](docs/images/home.png)\n\n"
        "![Tests](https://img.shields.io/badge/tests-passing-green)\n"
    )
    docs._cache.clear()

    body = client_in.get(reverse("docs:page", args=["guide"])).content.decode()
    image_url = reverse("docs:image", args=["home.png"])
    assert f'src="{image_url}"' in body
    assert "img.shields.io" not in body  # blocked by the page's policy: shown as a label
    assert ">Tests</span>" in body

    response = client_in.get(image_url)
    assert response.status_code == 200 and response["Content-Type"] == "image/png"

    images = reverse("docs:index") + "images/"
    assert client_in.get(images + "missing.png").status_code == 404
    assert client_in.get(images + "..%2F..%2FREADME.md").status_code == 404

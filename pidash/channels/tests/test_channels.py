"""The channel list: add, remove, and don't corrupt the file."""

import json

from django.urls import reverse

from pidash.services.catalog import get_service


def channels():
    return json.loads(get_service("timed").config and open(get_service("timed").config).read())


def test_the_list_is_shown(client_in):
    assert "First" in client_in.get(reverse("channels:page")).content.decode()


def test_a_channel_can_be_added(client_in):
    client_in.post(
        reverse("channels:add", args=["timed"]),
        {"id": "UC2", "name": "Second", "niche": "other things"},
    )
    assert [c["id"] for c in channels()["channels"]] == ["UC1", "UC2"]


def test_the_same_channel_is_not_added_twice(client_in):
    client_in.post(reverse("channels:add", args=["timed"]), {"id": "UC1", "name": "Again"})
    assert len(channels()["channels"]) == 1


def test_a_channel_without_a_name_is_refused(client_in):
    client_in.post(reverse("channels:add", args=["timed"]), {"id": "UC9", "name": ""})
    assert len(channels()["channels"]) == 1


def test_a_channel_can_be_removed(client_in):
    client_in.post(reverse("channels:remove", args=["timed"]), {"id": "UC1"})
    assert channels()["channels"] == []

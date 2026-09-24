"""Fixtures: a fake catalogue on disk, a signed-in client, and a silent systemd."""

import json
import os
from pathlib import Path

import pytest
from django.contrib.auth.models import User

from pidash.services import systemd


@pytest.fixture(autouse=True)
def service_root(tmp_path):
    """A fresh copy of the fake services' files for every test."""
    root = tmp_path / "services"
    os.environ["PIDASH_TEST_SERVICES_DIR"] = str(root)
    for name in ("always-bot", "timed-bot", "web-app"):
        (root / name / "prompts").mkdir(parents=True)
    (root / "always-bot" / "always.log").write_text(
        "2026-09-20 10:00:00 started\n2026-09-20 10:01:00 did a thing\nplain line\n"
    )
    (root / "always-bot" / "prompts" / "style.txt").write_text("Write nicely.\n")
    (root / "always-bot" / "prompts" / "style.default.txt").write_text("Write plainly.\n")
    (root / "always-bot" / "prompts" / "digest.default.txt").write_text("Summarise {text}.\n")
    (root / "timed-bot" / "timed.log").write_text("2026-09-20 09:00:00 ran\n")
    (root / "timed-bot" / "channels.json").write_text(
        json.dumps({"channels": [{"id": "UC1", "name": "First", "niche": "things"}]})
    )
    return root


@pytest.fixture(autouse=True)
def catalogue(settings, service_root, tmp_path):
    """Every test uses the fake services and its own shared-config folder."""
    settings.PIDASH_SERVICES_MODULE = "config.test_services"
    settings.PIDASH_SHARED_CONFIG_DIR = tmp_path / "shared"
    return service_root


@pytest.fixture
def user(db):
    return User.objects.create_user("owner", "owner@example.invalid", "a-long-test-password")


@pytest.fixture
def client_in(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def fake_systemd(monkeypatch):
    """Record what would have been run, and answer as if everything is fine."""
    calls = []

    def fake_run(argv, timeout=15):
        calls.append(argv)
        if "show" in argv:
            units = [a for a in argv if a.endswith((".service", ".timer"))]
            blocks = [
                "ActiveState=active\nSubState=running\nUnitFileState=enabled\n"
                "ActiveEnterTimestamp=Sun 2026-09-20 08:00:00 CEST\nMemoryCurrent=52428800\n"
                "Result=success"
                for _unit in units
            ]
            return 0, "\n\n".join(blocks), ""
        if "list-timers" in argv:
            return 0, "[]", ""
        if argv and argv[0] == "tail":
            return 0, Path(argv[-1]).read_text().strip() if Path(argv[-1]).is_file() else "", ""
        return 0, "", ""

    monkeypatch.setattr(systemd, "run", fake_run)
    # Nothing in the tests should reach out over the network.
    monkeypatch.setattr(systemd, "is_healthy", lambda url, timeout=4: True)
    monkeypatch.setattr("pidash.core.files.run", fake_run)
    return calls

"""Who gets each bot's e-mail.

This used to live inside every bot's .env, next to its API keys — which meant the
dashboard had to be able to read those files. It now lives in one small file the
dashboard owns and the bots read.
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings

from pidash.core.files import read_json, write_json

FILENAME = "recipients.json"


def path() -> Path:
    return Path(settings.PIDASH_SHARED_CONFIG_DIR) / FILENAME


def all_recipients() -> dict[str, str]:
    return read_json(path(), {}) or {}


def get(service_id: str) -> str:
    return all_recipients().get(service_id, "")


def set_for(service_id: str, addresses: str) -> None:
    current = all_recipients()
    current[service_id] = addresses.strip()
    target = path()
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, current)

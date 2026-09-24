"""A fake service catalogue for the tests, laid out in a temporary folder."""

import os


def __getattr__(name):
    """Build SERVICES on every access, so each test can point ROOT at its own folder."""
    if name == "SERVICES":
        return _services(os.environ["PIDASH_TEST_SERVICES_DIR"])
    raise AttributeError(name)


def _services(ROOT):  # noqa: N803 - reads like the real config file below
    return [
        {
            "id": "always",
            "name": "Always Bot",
            "blurb": "Runs all the time.",
            "kind": "resident",
            "unit": "always-bot",
            "timer": None,
            "dir": f"{ROOT}/always-bot",
            "log": "always.log",
            "runs": [{"label": "Test run", "mode": "test"}],
            "config": None,
            "prompts": [
                {"id": "style", "label": "Style", "desc": "How it writes.", "vars": []},
                {"id": "digest", "label": "Digest", "desc": "Needs the text.", "vars": ["text"]},
            ],
            "email": True,
            "health": None,
            "url": None,
        },
        {
            "id": "timed",
            "name": "Timed Bot",
            "blurb": "Runs on a timer.",
            "kind": "scheduled",
            "unit": "timed-bot",
            "timer": "timed-bot",
            "dir": f"{ROOT}/timed-bot",
            "log": "timed.log",
            "runs": [{"label": "Full run", "mode": ""}],
            "config": f"{ROOT}/timed-bot/channels.json",
            "prompts": [],
            "email": False,
            "health": None,
            "url": None,
        },
        {
            "id": "web",
            "name": "Web App",
            "blurb": "A web app with a health check.",
            "kind": "app",
            "unit": "web-app",
            "timer": None,
            "dir": f"{ROOT}/web-app",
            "log": "web.log",
            "runs": [],
            "config": None,
            "prompts": [],
            "email": False,
            "health": "http://127.0.0.1:9/healthz",
            "url": None,
        },
    ]

"""What the dashboard manages. One entry per service — nothing else needs changing.

Adding a service: append a dict below. Its card, log view, prompts, schedule row and
controls all follow from this. A start-up check refuses to run if an entry is malformed,
so a typo shows up immediately rather than as a blank page.

Fields
  id       short slug used in URLs
  name     what the card says
  blurb    one line under the name
  kind     "resident"  — always running; start/stop/restart act on the service
           "scheduled" — fired by a timer; start/stop/restart act on the timer
           "app"       — a web app; like resident, but has a health check and a link
  unit     systemd unit base name (without .service)
  timer    systemd timer base name (without .timer), or None
  dir      working folder, used for relative log paths
  log      log file, absolute or relative to dir
  runs     manual runs, each {"label", "mode"}. A mode starts unit@mode.service,
           an empty mode starts unit.service — so every run goes through systemd.
  config   JSON file the dashboard may edit (the channel list), or None
  prompts  editable prompt files in <dir>/prompts/. vars lists the placeholders the
           text must keep; saving is refused if one goes missing.
  email    True when the bot sends e-mail, so it shows on the recipients page
  health   URL that should answer 200, or None
  url      where to open the app itself, or None
"""

BOTS_DIR = "/home/acika/bots"

SERVICES = [
    {
        "id": "kevin",
        "name": "Kevin Bot",
        "blurb": "Summarizes new videos from one channel, hourly.",
        "kind": "resident",
        "unit": "kevin-bot",
        "timer": None,
        "dir": f"{BOTS_DIR}/kevin-bot",
        "log": "kevin_bot.log",
        "runs": [{"label": "Test run", "mode": "test"}],
        "config": None,
        "prompts": [
            {
                "id": "summary_style",
                "label": "Summary style",
                "desc": (
                    "The sections of the email and the tone of the summary. Used for every "
                    "video, short or long — both code paths append this same spec, so one "
                    "edit changes them all."
                ),
                "vars": [],
            },
        ],
        "email": True,
        "health": None,
        "url": None,
    },
    {
        "id": "news",
        "name": "News Bot",
        "blurb": "Morning brief and evening recap, twice daily.",
        "kind": "scheduled",
        "unit": "news-bot",
        "timer": "news-bot",
        "dir": f"{BOTS_DIR}/news-bot",
        "log": "news_bot.log",
        "runs": [
            {"label": "Morning brief", "mode": "morning"},
            {"label": "Evening recap", "mode": "evening"},
        ],
        "config": None,
        "prompts": [
            {
                "id": "morning",
                "label": "Morning brief",
                "desc": (
                    "Sections, ordering and tone of the 08:00 briefing. The date and the "
                    "fetched headlines are attached automatically."
                ),
                "vars": [],
            },
            {
                "id": "evening",
                "label": "Evening recap",
                "desc": (
                    "Sections, ordering and tone of the 20:00 recap. The date and the "
                    "fetched headlines are attached automatically."
                ),
                "vars": [],
            },
        ],
        "email": True,
        "health": None,
        "url": None,
    },
    {
        "id": "content",
        "name": "Content Bot",
        "blurb": "Scans channels for clip candidates, three times daily.",
        "kind": "scheduled",
        "unit": "content-bot",
        "timer": "content-bot",
        "dir": f"{BOTS_DIR}/content-bot",
        "log": "content_bot.log",
        "runs": [
            {"label": "Full run", "mode": ""},
            {"label": "Test run", "mode": "test"},
        ],
        "config": f"{BOTS_DIR}/content-bot/channels.json",
        "prompts": [
            {
                "id": "clip_finder",
                "label": "Clip finder",
                "desc": (
                    "The criteria for what counts as a Short-worthy moment, and the output "
                    "format for each clip. This is the one that decides what the bot flags."
                ),
                "vars": [],
            },
        ],
        "email": True,
        "health": None,
        "url": None,
    },
    {
        "id": "avifly",
        "name": "Avifly Tracker",
        "blurb": "The spraying business app: jobs, money and analytics.",
        "kind": "app",
        "unit": "avifly",
        "timer": None,
        "dir": "/home/acika/avifly-tracker",
        "log": "var/log/avifly.log",
        "runs": [],
        "config": None,
        "prompts": [],
        "health": "http://127.0.0.1:8000/healthz",
        "url": None,  # set PIDASH_AVIFLY_URL in .env to link out to it
    },
    {
        "id": "updater",
        "name": "Dependency updater",
        "blurb": "Updates the system and every venv every 5 days, with rollback.",
        "kind": "scheduled",
        "unit": "bot-updater",
        "timer": "bot-updater",
        "dir": f"{BOTS_DIR}/updater",
        "log": "updater.log",
        "runs": [{"label": "Update now", "mode": ""}],
        "config": None,
        "prompts": [],
        "health": None,
        "url": None,
    },
]

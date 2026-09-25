# Pi control

A small dashboard for the services on this Raspberry Pi: the bots, the Avifly tracker and
the dependency updater. Server-rendered Django, dark, and built to be used from a phone.

It replaced the older FastAPI dashboard in September 2026, keeping every button it had
and serving on the same port (5000).

## What it does

- **Cards for every service** — running or scheduled, uptime and memory, next run, last log
  line, and a health check for web apps. Start, stop, restart, and the manual runs each bot
  offers.
- **Logs** — pick a service, tail as many lines as you like, filter, auto-refresh, clear.
- **Prompts** — edit what each bot asks the model, with the shipped default one click away.
  A prompt that would lose a required placeholder is refused.
- **Channels** — the list the content bot watches.
- **Schedule** — when each timed job runs next, and when it last ran.
- **System** — CPU, temperature, memory, disk, uptime; start/stop/restart everything;
  clear all logs; run the updater; reboot or shut down.
- **Settings** — who receives each bot's e-mail.
- **Alerts** — a push message when a service fails, and another when it recovers.
- **Documentation** — this page and the operator's cheat sheet, rendered inside the app
  under Settings, straight from the Markdown in this project so they can't go stale.

## How it's built

One Django project, one module per feature (`services`, `logs`, `prompts`, `channels`,
`recipients`, `system`, `alerts`, `docs`). Each module registers its own menu entry, pages and
panels, so the navigation and the overview are assembled from whatever is installed — the
same idea as the Avifly tracker.

**Everything it manages comes from `config/services.py`.** Adding a service is one entry
there: its card, log view, prompts, schedule row, controls, sudo rules and file permissions
all follow. `manage.py print_sudoers` and `manage.py print_paths` read that file, so the
installer never needs editing.

No front-end build step: Bootstrap 5.3 in dark mode, a little HTMX for live status, and
about forty lines of JavaScript.

## How it runs

- Its own unprivileged account (`pidash`), which may control **exactly** the units listed
  in `config/services.py` through one generated sudoers file, and nothing else. It cannot
  read the bots' `.env` files or the tracker's database.
- Reaching the bots' prompts and configs goes through a shared `botcfg` group; logs and
  folders are reached with per-file ACLs, so nothing else in your home is exposed.
- Recipients live in `/etc/bots/recipients.json`, which the dashboard owns and the bots
  read — that is why it no longer needs to touch a bot's `.env`.
- Manual runs go through systemd (`kevin-bot@test.service`), so they run as the right user
  with the right environment and show up in the journal like any other run.

## Commands

```bash
make check            # lint + tests
make run              # development server on :5002 with its own data
make user u=<name>    # add a login
make manage cmd="…"   # any manage.py command, as the service account
make sudoers          # show the sudo rules this dashboard needs
./deploy/install.sh   # set up or update everything (safe to re-run)
```

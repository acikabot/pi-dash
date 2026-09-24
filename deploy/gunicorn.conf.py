"""Gunicorn settings. Values come from the environment / .env (see .env.example)."""

import os
from pathlib import Path

import environ

environ.Env.read_env(Path(__file__).resolve().parent.parent / ".env")

bind = os.environ.get("PIDASH_BIND", "127.0.0.1:5001")
workers = int(os.environ.get("PIDASH_WORKERS", "2"))
threads = 2
timeout = 60
graceful_timeout = 20
max_requests = 1000
max_requests_jitter = 100
accesslog = "-"
errorlog = "-"
forwarded_allow_ips = "127.0.0.1,::1"
# No runtime control socket (gunicorn 26+): nothing uses it, and the service account
# has no home directory to put it in.
control_socket_disable = True

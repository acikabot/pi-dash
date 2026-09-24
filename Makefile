# Everyday commands. Run `make help` to list them.
PY := .venv/bin/python

SERVICE_USER := $(shell systemctl show --property=User --value pidash.service 2>/dev/null)
AS_SERVICE := $(if $(filter-out $(shell id -un),$(SERVICE_USER)),sudo -u $(SERVICE_USER))
MANAGE := $(AS_SERVICE) $(PY) manage.py

DEV_ENV := PIDASH_DEBUG=true PIDASH_DATA_DIR=var-dev PIDASH_ALLOWED_HOSTS='*' \
	PIDASH_SECRET_KEY=development-only

.PHONY: help install test lint format check run manage user shell update sudoers

help:  ## Show this help
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

install:  ## Set it up and run it as a service (Raspberry Pi)
	./deploy/install.sh

test:  ## Run the test suite
	.venv/bin/pytest

lint:  ## Check code style
	.venv/bin/ruff check . && .venv/bin/ruff format --check .

format:  ## Fix code style
	.venv/bin/ruff check --fix . && .venv/bin/ruff format .

check: lint test  ## Lint + tests

run:  ## Development server on port 5002, with its own data in var-dev/
	$(DEV_ENV) $(PY) manage.py migrate --noinput --verbosity 0
	$(DEV_ENV) $(PY) manage.py runserver 0.0.0.0:5002

manage:  ## Any manage.py command (live): make manage cmd="check_services"
	@test -n "$(cmd)" || { echo 'Usage: make manage cmd="<command>"'; exit 2; }
	$(MANAGE) $(cmd)

user:  ## Add a login: make user u=<username>
	@test -n "$(u)" || { echo 'Usage: make user u=<username>'; exit 2; }
	$(MANAGE) createsuperuser --username $(u)

shell:  ## Python shell with the app loaded
	$(MANAGE) shell

sudoers:  ## Show the sudo rules this dashboard needs
	$(PY) manage.py print_sudoers --user $(if $(SERVICE_USER),$(SERVICE_USER),pidash)

update:  ## Reinstall dependencies, migrate, collect static and restart
	./deploy/install.sh

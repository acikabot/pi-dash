#!/usr/bin/env bash
# Set the dashboard up on the Pi (safe to re-run).
#
# It runs as its own account (PIDASH_SERVICE_USER, default "pidash") which can:
#   * control exactly the units the service catalogue lists, through one sudoers file
#   * read the bots' logs and write their prompts and configs, through a shared group
#   * write its own data folder and the shared config folder
# and nothing else. Your account keeps owning the code.
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEV_USER="$(id -un)"
SERVICE_USER="${PIDASH_SERVICE_USER:-pidash}"
SHARED_GROUP="${PIDASH_SHARED_GROUP:-botcfg}"
SHARED_DIR="${PIDASH_SHARED_CONFIG_DIR:-/etc/bots}"
BOTS_DIR="${PIDASH_BOTS_DIR:-/home/acika/bots}"
cd "$APP_DIR"

as_service() { sudo -u "$SERVICE_USER" "$@"; }

echo "==> Python environment"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

if [ ! -f .env ]; then
  echo "==> Creating .env"
  cp .env.example .env
  SECRET="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(50))')"
  sed -i "s|^PIDASH_SECRET_KEY=.*|PIDASH_SECRET_KEY=${SECRET}|" .env
  chmod 600 .env
fi

echo "==> Accounts and groups (needs sudo)"
id -u "$SERVICE_USER" >/dev/null 2>&1 || sudo useradd --system --user-group \
  --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin \
  --comment "Pi dashboard" "$SERVICE_USER"
getent group "$SHARED_GROUP" >/dev/null || sudo groupadd --system "$SHARED_GROUP"
# The dashboard and you both work on the bots' prompts and configs.
sudo usermod --append --groups "$SHARED_GROUP,$SERVICE_USER" "$DEV_USER"
sudo usermod --append --groups "$SHARED_GROUP" "$SERVICE_USER"

grant_traverse() {  # walk into a folder without being able to read its contents
  local dir="$1"
  while [ "$dir" != "/" ] && [ -n "$dir" ]; do
    sudo -u "$SERVICE_USER" test -x "$dir" || sudo setfacl -m "u:${SERVICE_USER}:--x" "$dir"
    dir="$(dirname "$dir")"
  done
}

echo "==> Code and data"
command -v setfacl >/dev/null || sudo apt-get install -y -qq acl
grant_traverse "$(dirname "$APP_DIR")"   # a private home folder is only walked through
sudo chgrp "$SERVICE_USER" "$APP_DIR" .env
chmod 750 "$APP_DIR"
chmod 640 .env
mkdir -p var
sudo chown -R "$SERVICE_USER:$SERVICE_USER" var
sudo chmod -R u=rwX,g=rX,o= var

echo "==> Shared config folder ${SHARED_DIR}"
sudo mkdir -p "$SHARED_DIR"
sudo chown "$SERVICE_USER:$SHARED_GROUP" "$SHARED_DIR"
sudo chmod 2750 "$SHARED_DIR"   # setgid: the bots' group can read what lands here

echo "==> Access to the services' files"
# Every path comes from config/services.py, so a new service needs no changes here.
as_service .venv/bin/python manage.py print_paths | while IFS=$'\t' read -r kind path; do
  case "$kind" in
    dir)
      [ -d "$path" ] || continue
      grant_traverse "$(dirname "$path")"
      sudo setfacl -m "u:${SERVICE_USER}:r-x" "$path"
      ;;
    log)
      [ -e "$path" ] || continue
      folder="$(dirname "$path")"
      grant_traverse "$folder"        # e.g. a tracker's var/ folder on the way
      sudo setfacl -m "u:${SERVICE_USER}:r-x" "$folder"
      # A rotated log is a new file, so the folder hands the right rights to new files too.
      sudo setfacl -d -m "u:${SERVICE_USER}:rw-" "$folder" 2>/dev/null || true
      sudo setfacl -m "u:${SERVICE_USER}:rw-" "$path"
      ;;
    prompts)
      [ -d "$path" ] || continue
      sudo chgrp -R "$SHARED_GROUP" "$path"
      sudo chmod -R g+rw "$path"
      sudo chmod g+s "$path"          # new prompt files inherit the group
      ;;
    config)
      [ -f "$path" ] || continue
      for file in "$path" "$path".bak; do
        [ -f "$file" ] || continue
        sudo chgrp "$SHARED_GROUP" "$file"
        sudo chmod g+rw "$file"
      done
      ;;
  esac
done

echo "==> Manual-run units for the bots"
for unit in deploy/bots/*@.service; do
  [ -f "$unit" ] || continue
  sudo install -m 644 "$unit" "/etc/systemd/system/$(basename "$unit")"
done

echo "==> Sudo rules"
TMP_RULES="$(mktemp)"
as_service .venv/bin/python manage.py print_sudoers --user "$SERVICE_USER" > "$TMP_RULES"
sudo visudo -cqf "$TMP_RULES"           # refuse to install a file sudo can't parse
sudo install -m 440 -o root -g root "$TMP_RULES" /etc/sudoers.d/pidash
rm -f "$TMP_RULES"

echo "==> Database and static files"
as_service .venv/bin/python manage.py migrate --noinput
as_service .venv/bin/python manage.py collectstatic --noinput --verbosity 0

echo "==> systemd services"
for unit in pidash.service pidash-check.service; do
  sed -e "s|__APP_DIR__|${APP_DIR}|g" -e "s|__USER__|${SERVICE_USER}|g" \
      -e "s|__SHARED_DIR__|${SHARED_DIR}|g" -e "s|__BOTS_DIR__|${BOTS_DIR}|g" \
      "deploy/${unit}" | sudo tee "/etc/systemd/system/${unit}" >/dev/null
done
sudo install -m 644 deploy/pidash-check.timer /etc/systemd/system/pidash-check.timer
sudo systemctl daemon-reload
sudo systemctl enable --now pidash.service pidash-check.timer
sudo systemctl restart pidash.service
sleep 2
systemctl --no-pager --lines=0 status pidash.service || true

PORT="$(grep -E '^PIDASH_BIND=' .env | sed 's/.*://')"
echo
echo "Done. The dashboard is on port ${PORT:-5001}."
echo "Make yourself an account:  make user u=<username>"
echo "Log out and back in once so your account picks up the '${SHARED_GROUP}' group."

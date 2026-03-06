#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Ana — Raspberry Pi auto-start setup
# Run once as the user who will own the bot process:
#   chmod +x setup_autostart.sh && ./setup_autostart.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
SERVICE_NAME="ana-bot"
BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # absolute path to this repo
VENV_DIR="$BOT_DIR/.venv"
PYTHON_BIN="$(command -v python3)"
RUN_USER="$(whoami)"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✔]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✘]${NC} $*" >&2; exit 1; }

echo ""
echo "  Ana Bot — Raspberry Pi autostart setup"
echo "  ======================================="
echo "  Bot directory : $BOT_DIR"
echo "  Running as    : $RUN_USER"
echo "  Python        : $PYTHON_BIN"
echo ""

# ── 1. Sanity checks ──────────────────────────────────────────────────────────
[[ -f "$BOT_DIR/main.py" ]]        || error "main.py not found in $BOT_DIR — run this script from the Ana repo."
[[ -f "$BOT_DIR/requirements.txt" ]] || error "requirements.txt not found in $BOT_DIR."
[[ -f "$BOT_DIR/.env" ]]           || warn  ".env file not found — bot will fail to start without DISCORD_TOKEN etc."
command -v python3 &>/dev/null      || error "python3 not found. Install it with: sudo apt install python3"
command -v pip3   &>/dev/null      || error "pip3 not found. Install it with: sudo apt install python3-pip"

# ── 2. Create virtual environment ─────────────────────────────────────────────
if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating virtual environment at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
else
    info "Virtual environment already exists at $VENV_DIR — skipping creation."
fi

# ── 3. Install / upgrade dependencies ────────────────────────────────────────
info "Installing dependencies from requirements.txt ..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r "$BOT_DIR/requirements.txt" --quiet
info "Dependencies installed."

# ── 4. Write systemd service file ────────────────────────────────────────────
info "Writing systemd service to $SERVICE_FILE ..."

# Requires sudo — prompt once here
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Ana Discord Bot
# Wait for the network stack to be fully up before starting
After=network-online.target
Wants=network-online.target
# Attempt to restart up to 5 times if the network isn't ready immediately
StartLimitIntervalSec=120
StartLimitBurst=5

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${BOT_DIR}
EnvironmentFile=${BOT_DIR}/.env
ExecStart=${VENV_DIR}/bin/python ${BOT_DIR}/main.py

# Restart automatically on crash or non-zero exit
Restart=on-failure
RestartSec=10s

# Allow the process to write logs via stdout/stderr (viewable with journalctl)
StandardOutput=journal
StandardError=journal

# Prevent runaway restarts: if it crashes 5× in 2 min, stop trying
# (avoids hammering the Discord API with bad credentials)
# Increase these if your Pi has intermittent connectivity
# StartLimitIntervalSec and StartLimitBurst above handle this

[Install]
WantedBy=multi-user.target
EOF

# ── 5. Reload systemd, enable + start ────────────────────────────────────────
info "Reloading systemd daemon ..."
sudo systemctl daemon-reload

info "Enabling ${SERVICE_NAME} to start on every boot ..."
sudo systemctl enable "${SERVICE_NAME}"

info "Starting ${SERVICE_NAME} now ..."
sudo systemctl restart "${SERVICE_NAME}"

# ── 6. Status check ───────────────────────────────────────────────────────────
sleep 2
if sudo systemctl is-active --quiet "${SERVICE_NAME}"; then
    info "Ana is running! 🎉"
else
    warn "Service started but may have exited. Check logs with:"
    echo ""
    echo "    journalctl -u ${SERVICE_NAME} -n 50 --no-pager"
    echo ""
fi

echo ""
echo "  Useful commands"
echo "  ───────────────"
echo "  View live logs   :  journalctl -u ${SERVICE_NAME} -f"
echo "  Stop the bot     :  sudo systemctl stop ${SERVICE_NAME}"
echo "  Start the bot    :  sudo systemctl start ${SERVICE_NAME}"
echo "  Restart the bot  :  sudo systemctl restart ${SERVICE_NAME}"
echo "  Disable autostart:  sudo systemctl disable ${SERVICE_NAME}"
echo "  Remove service   :  sudo rm $SERVICE_FILE && sudo systemctl daemon-reload"
echo ""

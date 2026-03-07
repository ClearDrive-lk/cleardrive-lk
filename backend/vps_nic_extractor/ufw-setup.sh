#!/usr/bin/env bash
set -euo pipefail

# CD-51.3 firewall setup helper.
# Usage:
#   RENDER_IP=x.x.x.x YOUR_IP=y.y.y.y ./ufw-setup.sh

if [[ -z "${RENDER_IP:-}" || -z "${YOUR_IP:-}" ]]; then
  echo "RENDER_IP and YOUR_IP must be set"
  exit 1
fi

sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from "${YOUR_IP}" to any port 22 proto tcp
sudo ufw allow from "${RENDER_IP}" to any port 8001 proto tcp
sudo ufw --force enable
sudo ufw status verbose

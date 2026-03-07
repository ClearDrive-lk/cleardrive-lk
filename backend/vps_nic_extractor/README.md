# CD-51 VPS NIC Extractor

This folder contains deployable assets for CD-51 local VPS NIC extraction.

## Coverage by subtask

- `CD-51.1` Provision DigitalOcean droplet: manual infrastructure step (see commands below).
- `CD-51.2` Install Ollama + pull `minicpm-v`: manual VPS step.
- `CD-51.3` Firewall whitelist Render IP on port `8001`: use `ufw-setup.sh`.
- `CD-51.4` FastAPI `/extract/nic` endpoint: implemented in `main.py`.
- `CD-51.5` `X-Internal-Secret` auth: enforced in `main.py`.
- `CD-51.6` Structured JSON schema validation: enforced with Pydantic in `main.py`.
- `CD-51.7` Memory-only image handling: `BytesIO` only, no file writes in `main.py`.
- `CD-51.8` `VPS_URL` + `VPS_SECRET` env vars: added to backend env example files.

## VPS deployment steps (manual)

1. Provision droplet:
```bash
doctl compute droplet create cleardrive-nic-extraction \
  --region sgp1 \
  --size s-2vcpu-4gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys YOUR_SSH_KEY_ID \
  --enable-ipv6 \
  --tag-names production,nic-extraction
```

2. Install runtime:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip curl ufw fail2ban
curl -fsSL https://ollama.com/install.sh | sh
ollama pull minicpm-v
```

3. Deploy service:
```bash
mkdir -p /home/ollama/nic-extractor
cd /home/ollama/nic-extractor
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env INTERNAL_SECRET
sudo cp nic-extractor.service /etc/systemd/system/nic-extractor.service
sudo systemctl daemon-reload
sudo systemctl enable nic-extractor
sudo systemctl start nic-extractor
```

4. Configure firewall:
```bash
RENDER_IP=<render-ip> YOUR_IP=<your-ip> ./ufw-setup.sh
```

## Render variables

Set in Render backend environment:

- `VPS_URL=http://<vps-ip>:8001`
- `VPS_SECRET=<shared-secret>`
- `KYC_VPS_TIMEOUT_SECONDS=60`
- `KYC_VPS_MAX_RETRIES=1`

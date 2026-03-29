# NIC Demo Checklist

Use this sequence for the lecturer demo.

## Demo mode

Recommended for local demo:

- ClearDrive backend runs in Docker on your laptop.
- NIC extractor runs on your laptop on port `8001`.
- Ollama runs on your laptop on port `11434`.
- Backend calls extractor through `http://host.docker.internal:8001`.

Use ngrok only if you want a public server such as `cleardrive.lk` to call your laptop.

## 1. Start Ollama

Open PowerShell:

```powershell
ollama serve
```

Open another PowerShell:

```powershell
ollama list
```

If `minicpm-v` is missing:

```powershell
ollama pull minicpm-v
```

Health check:

```powershell
curl.exe http://127.0.0.1:11434/api/tags
```

## 2. Start NIC extractor

Open PowerShell:

```powershell
cd E:\projects\cleardrive-lk\backend\vps_nic_extractor
.\venv\Scripts\Activate.ps1
$env:INTERNAL_SECRET="1234"
$env:OLLAMA_URL="http://127.0.0.1:11434"
$env:OLLAMA_MODEL="minicpm-v:latest"
$env:OLLAMA_TIMEOUT_SECONDS="180"
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

Health check:

```powershell
curl.exe -H "X-Internal-Secret: 1234" http://127.0.0.1:8001/health
```

Expected result:

- status is `healthy`
- `minicpm_v_available` is `true`

## 3. Start ClearDrive backend

From repo root:

```powershell
docker compose up -d --build
```

Backend should use these values from [backend/.env](E:/projects/cleardrive-lk/backend/.env):

```env
VPS_URL=http://host.docker.internal:8001
VPS_SECRET=1234
KYC_VPS_TIMEOUT_SECONDS=60
KYC_VPS_MAX_RETRIES=1
```

## 4. Optional: start ngrok

Only needed if a public site must call your laptop.

```powershell
ngrok http 8001
```

If ngrok is used, update [backend/.env](E:/projects/cleardrive-lk/backend/.env):

```env
VPS_URL=https://your-real-ngrok-url.ngrok-free.dev
```

Then restart backend:

```powershell
docker compose up -d --build backend
```

## 5. Quick direct extraction test

Front:

```powershell
curl.exe -X POST `
  -H "X-Internal-Secret: 1234" `
  -H "X-Side: front" `
  -F "image=@C:\Users\malit\Downloads\New folder (2)\Front.jpeg;type=image/jpeg" `
  http://127.0.0.1:8001/extract/nic
```

Back:

```powershell
curl.exe -X POST `
  -H "X-Internal-Secret: 1234" `
  -H "X-Side: back" `
  -F "image=@C:\Users\malit\Downloads\New folder (2)\Back.png;type=image/png" `
  http://127.0.0.1:8001/extract/nic
```

## 6. What to say in the demo

- User uploads NIC images in ClearDrive.
- ClearDrive backend sends the image to the NIC extraction service.
- The extractor sends the image to local Ollama running `minicpm-v`.
- The model returns structured JSON.
- ClearDrive uses that JSON in the KYC flow.

## 7. Do not close these windows

- `ollama serve`
- NIC extractor terminal
- Docker backend
- ngrok terminal if using ngrok

## 8. Fast recovery if demo fails

Check Ollama:

```powershell
curl.exe http://127.0.0.1:11434/api/tags
```

Check extractor:

```powershell
curl.exe -H "X-Internal-Secret: 1234" http://127.0.0.1:8001/health
```

Restart backend:

```powershell
docker compose up -d --build backend
```

If ngrok URL changed, update `VPS_URL` and restart backend again.

# Weinregal Backend

GPT-4 Vision Backend für die Weinregal-App – analysiert Weinetiketten per KI.

## Deployment auf Render.com

1. Dieses Repository auf GitHub pushen
2. Auf [render.com](https://render.com) einloggen → **New Web Service**
3. Repository verbinden
4. Unter **Environment Variables** eintragen:
   - `OPENAI_API_KEY` = dein OpenAI API-Key
5. Deploy klicken

## API Endpoints

- `GET /health` – Status-Check
- `POST /analyze` – Weinetikett analysieren
  - Body: `{"image": "<base64-encoded-jpeg>"}`
  - Response: `{"success": true, "wine": {...}}`

## Lokaler Start

```bash
pip install -r requirements.txt
OPENAI_API_KEY=sk-... python server.py
```

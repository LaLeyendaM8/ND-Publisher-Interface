# ND Publisher API

## Local setup

```powershell
cd services/api
py -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Set `OPENAI_API_KEY` in `services/api/.env`.

## Endpoints

- `GET /health`
- `GET /tools`

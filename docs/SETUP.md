# Setup Notes

## Workspace

Root: `C:\Users\alina\Desktop\NEGATIVE DIALEKTIK\ND - Publisher Interface`

Current structure:

- `apps/web` (Next.js frontend scaffold)
- `services/api` (FastAPI backend scaffold)
- `packages` (shared code later)
- `docs` (project docs)
- `scripts` (utility scripts later)

## Node and npm on Windows PowerShell

On this machine, `npm` via `npm.ps1` is blocked by execution policy.

Use:

```powershell
npm.cmd -v
```

If you want normal `npm` commands in PowerShell:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Install web dependencies

```powershell
cd apps/web
npm.cmd install --workspaces=false
npm.cmd run dev
```

## Install API dependencies

```powershell
cd services/api
py -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Then set `OPENAI_API_KEY` in `services/api/.env`.

## Verification

- Web: `http://localhost:3000`
- API health: `http://localhost:8000/health`
- API tools: `http://localhost:8000/tools`

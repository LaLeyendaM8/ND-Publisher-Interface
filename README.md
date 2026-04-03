# ND Publisher Interface

Internal ND app that unifies:

- Translation tool
- Bibliography tool
- Mechanical Lektorat tool

Roadmap:

- [PUBLISHER_INTERFACE_ROADMAP.md](./PUBLISHER_INTERFACE_ROADMAP.md)

Setup:

- [docs/SETUP.md](./docs/SETUP.md)

## Phase status

Current: Phase 1 bootstrap started.

Completed in this workspace:

- New project root and folder structure
- Next.js app scaffold in `apps/web`
- FastAPI scaffold in `services/api`
- Basic docs and root workspace config

## Quick start

```powershell
cd apps/web
npm.cmd run dev
```

```powershell
cd services/api
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

# ND Publisher Interface

Internal ND app that unifies:

- Translation tool
- Bibliography tool
- Mechanical Lektorat tool

Roadmap:

- [PUBLISHER_INTERFACE_ROADMAP.md](./PUBLISHER_INTERFACE_ROADMAP.md)

Setup:

- [docs/SETUP.md](./docs/SETUP.md)
- [docs/DEPLOYMENT_PHASE6.md](./docs/DEPLOYMENT_PHASE6.md)

## Phase status

Current: Phase 6 deployment preparation.

Completed in this workspace:

- New project root and folder structure
- Next.js ND-style app with Supabase login, protected routes, and project workflow
- FastAPI backend with DB-backed projects/files/jobs and role-aware access checks
- Supabase-aligned data model and migrations in `services/api/sql`
- API docker baseline and deployment docs for live rollout

## Quick start

```powershell
cd apps/web
npm.cmd run dev
```

```powershell
cd services/api
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

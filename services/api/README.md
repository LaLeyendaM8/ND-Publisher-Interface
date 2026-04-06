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
Optional for protected endpoints: set `APP_INTERNAL_API_TOKEN`.

## Docker run (deployment baseline)

```powershell
cd services/api
docker build -t nd-publisher-api .
docker run --rm -p 8000:8000 --env-file .env nd-publisher-api
```

## Endpoints

- `GET /health`
- `GET /auth/sync` (provisions/loads user + workspace membership from forwarded actor headers)
- `GET /tools`
- `POST /tools/run`
- `POST /tools/jobs` (enqueue async job)
- `GET /tools/jobs` (list jobs)
- `GET /tools/jobs/{job_id}` (job details/status)
- `GET /tools/jobs/{job_id}/artifacts/{artifact_index}` (download artifact)
- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `POST /projects/{project_id}/files` (multipart upload)
- `GET /projects/{project_id}/files`
- `POST /projects/{project_id}/jobs`
- `GET /projects/{project_id}/jobs`
- `GET /projects/{project_id}/jobs/{job_id}`

Example payload:

```json
{
  "tool": "translation",
  "input_path": "C:/path/to/book.pdf",
  "output_dir": "C:/path/to/output",
  "options": {
    "glossary_path": "C:/path/to/glossary.txt"
  }
}
```

Notes:

- `options` is validated per tool and unknown fields are rejected.
- `translation` and `bibliography` require a PDF input path.
- On business/runtime errors the endpoint returns a `JobResult` with `status: "failed"` and an error `message`.
- For async jobs, poll `GET /tools/jobs/{job_id}` and read `status` (`queued|running|done|failed`).
- If `APP_INTERNAL_API_TOKEN` is set, send header `X-Internal-Token: <token>` on protected endpoints.
- If requests come from web login, forward actor headers:
  - `X-User-Id`
  - `X-User-Email`
  - `X-User-Role` (`admin|editor|viewer`)
- `AUTH_AUTO_PROVISION_USERS=true` auto-creates workspace membership for new actor users.
- User role is stored in `workspace_members.role` (workspace-scoped), not in `users`.
- `/health` includes DB status (`database: ok|error|disabled`) for monitoring checks.
- API errors are standardized as:
  - `{ "ok": false, "error": { "code": "...", "message": "...", "details": ... } }`

## Phase 3 schema

- Initial SQL schema: `services/api/sql/001_initial_schema.sql`
- Schema notes: `docs/architecture/PHASE3_DATA_MODEL.md`
- Run migrations: `python -m tools.run_migrations`
- Run retention cleanup: `python -m tools.retention_cleanup`

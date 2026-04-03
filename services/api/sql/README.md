# SQL Migrations (Phase 3)

This folder contains raw SQL migrations for the API backend.

## Files

- `001_initial_schema.sql`: base schema for organizations, workspaces, users, projects, files, jobs, artifacts, glossaries, and audit events.

## Apply locally (example)

```bash
psql "$DATABASE_URL" -f services/api/sql/001_initial_schema.sql
```

## Notes

- Current API runtime still uses in-memory managers.
- Phase 3 next step is repository integration to persist projects/jobs/files/artifacts in Postgres.

## Retention cleanup

Run cleanup script manually:

```bash
python -m tools.retention_cleanup
```

Retention values are configured via `.env`:

- `RETENTION_ARTIFACT_DAYS`
- `RETENTION_FAILED_JOB_DAYS`
- `RETENTION_AUDIT_DAYS`

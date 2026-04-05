# Phase 3 Data Model (v1)

This document defines the first persistent data model for ND Publisher Interface.

## Goals

- Replace in-memory runtime state with database records.
- Keep one clear hierarchy for v1:
  - organization -> workspace -> project -> file -> job -> artifact
- Prepare for future multi-tenant SaaS without overengineering v1.

## Entity overview

- `organizations`: publisher organizations (tenant root).
- `workspaces`: operational space inside an organization.
- `users`: app user accounts linked to Supabase auth via `auth_user_id`.
- `workspace_members`: user membership and role in workspace.
- `projects`: work containers for uploaded files and runs.
- `files`: uploaded source files and metadata.
- `jobs`: async runs for translation/bibliography/proofcheck.
- `artifacts`: generated output files from jobs.
- `glossaries`: glossary files and metadata.
- `audit_events`: immutable log of key actions.

## Relationship map

- One organization has many workspaces.
- One workspace optionally stores `owner_user_id` for explicit ownership anchor.
- One workspace has many projects.
- One project has many files.
- One project has many jobs.
- One job has many artifacts.
- One workspace has many glossary records.
- Users connect to workspaces through `workspace_members`.
- Effective permissions come from `workspace_members.role` (not from a role column on `users`).

## Roles (v1)

- `owner`: full workspace control.
- `editor`: create projects, upload files, run tools.
- `viewer`: read-only access.

## Job lifecycle

- `queued`
- `running`
- `done`
- `failed`

## Tool enum

- `translation`
- `bibliography`
- `proofcheck`

## Artifact kind enum

- `docx`
- `jsonl`
- `xlsx`
- `json`
- `txt`
- `other`

## Naming conventions

- IDs: UUID primary keys.
- Timestamps: UTC (`TIMESTAMPTZ`).
- Paths: absolute paths in v1 local mode, object keys in remote mode.
- Soft delete: optional for future; v1 uses hard delete only on admin actions.

## Storage conventions (filesystem/object)

Root path is configurable via `APP_STORAGE_ROOT`.

Path pattern:

- `uploads/<workspace_id>/<project_id>/<file_id>_<safe_name>`
- `results/<workspace_id>/<project_id>/<job_id>/<artifact_kind>/<artifact_name>`
- `glossaries/<workspace_id>/<glossary_id>_<safe_name>`

## Retention rules (v1 defaults)

- Uploads: keep until explicit user deletion.
- Job artifacts: keep 180 days by default.
- Failed job logs: keep 30 days.
- Audit events: keep minimum 365 days.

## Migration approach

1. Create schema tables and enums.
2. Add repository layer in API services.
3. Swap in-memory project/job managers to DB-backed managers.
4. Keep API response contracts stable.

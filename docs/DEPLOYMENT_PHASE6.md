# Phase 6 Deployment Guide

Ziel: `app.negative-dialektik.com` (Web) + `api.negative-dialektik.com` (Backend) stabil live.

## 1) Architektur

- Web: Next.js auf Vercel (`apps/web`)
- API: FastAPI als eigener Service (Docker) auf Railway/Render/Fly
- DB/Auth: Supabase
- Domain-Split:
  - `www.negative-dialektik.com` bleibt Verlag/Shop
  - `app.negative-dialektik.com` fuer das interne Tool
  - `api.negative-dialektik.com` fuer FastAPI

## 2) Web Deployment (Vercel)

1. Repo in Vercel importieren.
2. Root Directory: `apps/web`
3. Environment Variables setzen:
   - `PUBLISHER_API_URL=https://api.negative-dialektik.com`
   - `PUBLISHER_API_TOKEN=<gleich wie API APP_INTERNAL_API_TOKEN>`
   - `NEXT_PUBLIC_SUPABASE_URL=<supabase-url>`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>`
4. Deploy triggern.

## 3) API Deployment (Docker Service)

`services/api/Dockerfile` ist vorbereitet.

Pflicht-Env:

- `APP_ENV=production`
- `APP_INTERNAL_API_TOKEN=<secret>`
- `OPENAI_API_KEY=<secret>`
- `DATABASE_URL=<supabase-pooler-url>`
- `NEXT_PUBLIC_SUPABASE_URL=<supabase-url>`
- `AUTH_AUTO_PROVISION_USERS=true`

Optional:

- `APP_STORAGE_ROOT` (Default im Container: `/app/data`)
- `RETENTION_ARTIFACT_DAYS`
- `RETENTION_FAILED_JOB_DAYS`
- `RETENTION_AUDIT_DAYS`

Nach erstem Deploy:

- Migrations ausfuehren: `python -m tools.run_migrations`

## 4) DNS / Subdomains

Du brauchst keine neue Domain.

Beim Domain-Provider:

- `app` als CNAME auf Vercel-Ziel
- `api` als CNAME/A auf API-Host

Dann in Vercel/API-Host jeweils die Custom Domain hinterlegen und TLS aktivieren.

## 5) Monitoring / Alerting (v1)

- Health endpoint: `GET /health`
- Uptime Monitor fuer:
  - `https://app.negative-dialektik.com/login`
  - `https://api.negative-dialektik.com/health`
- Alerts auf Email/Telegram/Slack

Empfehlung:

- Vercel Runtime Logs aktiv
- API-Host Logs + Error Alerts aktiv

## 6) Backups (v1)

- Supabase: automatische Backups aktivieren/prüfen.
- Storage: falls lokale Artifact-Files kritisch sind, auf persistentes Volume/Object Storage umstellen.
- Monatlich Restore-Test einer DB-Sicherung.

## 7) Live-Checkliste

1. Login mit `admin` funktioniert.
2. `viewer` kann lesen, aber nicht schreiben.
3. Projekt anlegen, Datei uploaden, Job starten, Artifact downloaden.
4. `/health` zeigt `database: ok`.
5. Logs zeigen keine 5xx-Spikes.

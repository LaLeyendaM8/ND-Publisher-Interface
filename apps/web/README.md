# ND Publisher Interface (Web)

Next.js frontend fuer das interne Verlagsinterface.

## Local Setup

1. `apps/web/.env.local` anlegen mit:

```env
PUBLISHER_API_URL=http://127.0.0.1:8000
PUBLISHER_API_TOKEN=your-internal-api-token
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

2. Development starten:

```bash
npm run dev
```

3. App im Browser oeffnen: [http://localhost:3000](http://localhost:3000)

## Phase-4 Scope

- ND-inspiriertes App-Design (Farben/Typografie)
- Supabase Login + geschuetzte App-Routen
- Navigation: Dashboard, Projekte, Tools, Dateien, Glossare, Einstellungen
- operative Projektansicht fuer Upload, Jobstart, Jobstatus und Artifact-Downloads
- Rollen in v1: `admin`/`editor` (write) und `viewer` (read-only)

## Quality Checks

```bash
npm run lint
npm run build
```

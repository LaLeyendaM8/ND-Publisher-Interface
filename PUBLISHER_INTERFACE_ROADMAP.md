# ND Publisher Interface Roadmap

Ziel: Ein internes Verlagsinterface mit Login, das die drei bestehenden Tools fuer Uebersetzung, Bibliography und mechanisches Lektorat in einer gemeinsamen Arbeitsoberflaeche zusammenfuehrt. Das System soll spaeter so erweiterbar sein, dass daraus ein Produkt fuer weitere Verlage werden kann.

## Fortschritt

- Status: `Phase 0 abgeschlossen`, `Phase 1 abgeschlossen`, `Phase 2 abgeschlossen`, `Phase 3 abgeschlossen`
- Aktueller Fokus: Phase 3, Datenmodell und Infrastruktur
- Erledigt in Phase 1: gemeinsames API/Core-Grundgeruest mit `files`, `chunking`, `retry`, `schemas`, Tool-Katalog
- Erledigt in Phase 1: Service-Adapter fuer `translation`, `bibliography`, `proofcheck` plus einheitlicher API-Run-Endpoint
- Erledigt in Phase 1: Option-Validierung pro Tool, sichere Fehlerpfade (`status=failed`) und Logging im Runner/API
- Erledigt im Phase-1->2 Uebergang: In-Memory Job-Store, `job_id`, Status-Lifecycle und asynchrone Job-Endpoints
- Erledigt in Phase 2: Projekt-Endpoints, Datei-Upload, Job-Start pro Projekt, Artifact-Download und Token-basierte Request-Protection (vorbereitet)
- Erledigt in Phase 2: projektgebundene Job-Abfragen (`/projects/{id}/jobs`, `/projects/{id}/jobs/{job_id}`)
- Erledigt in Phase 2: projektgebundene Datei-/Artifact-Downloads und Smoke-Test-Skript fuer End-to-End-Checks
- Erledigt in Phase 2: standardisierte API-Fehlerantworten (globales Error-Format fuer Validation/HTTP/Unhandled Exceptions)
- Erledigt in Phase 2: End-to-End Smoke-Test erfolgreich (`Projekt -> Upload -> Job -> Polling -> Ergebnis`)
- Erledigt in Phase 3: v1 Datenmodell spezifiziert (Entities, Beziehungen, Storage-Konventionen, Retention-Regeln)
- Erledigt in Phase 3: initiales Postgres-Schema als SQL-Migration angelegt (`services/api/sql/001_initial_schema.sql`)
- Erledigt in Phase 3: API-Manager DB-first gemacht (Projekte/Dateien/Jobs in Postgres, mit Fallback)
- Erledigt in Phase 3: Audit-Events in zentrale Flows integriert (`project.created`, `file.uploaded`, `job.queued`, `job.finished`)
- Erledigt in Phase 3: Retention/Cleanup-Skript implementiert (`tools.retention_cleanup`)

## Produktziel

- Interne Web-App im ND-Stil unter spaeterer eigener App-Subdomain.
- Nutzer koennen sich einloggen, Projekte anlegen, Dateien hochladen, Jobs starten und Ergebnisse herunterladen.
- Die drei bestehenden Python-Tools bleiben zunaechst die fachliche Engine.
- Die Architektur wird von Anfang an so angelegt, dass spaeter Mehrnutzerbetrieb, Rollen, Workspaces und SaaS moeglich sind.

## Leitprinzipien

- Erst ein gutes internes Tool bauen, dann verallgemeinern.
- Fachlogik nicht sofort nach JavaScript umschreiben, sondern zunaechst in Python kapseln.
- Frontend in Next.js, weil das bestehende Know-how dort liegt.
- Klare Trennung zwischen Marketing-/Shop-Seite und Arbeits-App.
- Sicherheit, Nachvollziehbarkeit und Dateiorganisation frueh mitdenken.

## Phase 0: Grundlagen und Entscheidungsvorbereitung

Ziel: Den bestehenden Stand sauber erfassen und die gemeinsame Struktur fuer die drei Tools definieren.

Aufgaben:

- Die drei bestehenden Skripte fachlich vergleichen und gemeinsame Pipeline-Bausteine dokumentieren.
- Inputs, Outputs und Dateiformate aller drei Tools festhalten.
- Risiken dokumentieren: API-Key-Handling, Encodings, Resume-Logik, lange Laufzeiten, Dateispeicherung.
- Gemeinsame Begriffe festlegen: `workspace`, `project`, `job`, `artifact`, `tool`.
- Entscheidung treffen, welche Version `v1` wirklich koennen muss und was bewusst spaeter kommt.

Ergebnis:

- Ein abgestimmtes Zielbild fuer `v1`.
- Eine Liste gemeinsamer Backend-Bausteine.

## Phase 1: Python-Tools produktionsfaehig machen

Ziel: Aus drei lokalen CLI-Skripten einen gemeinsamen, stabilen Python-Kern machen.

Aufgaben:

- Gemeinsame Utility-Module auslagern:
  - Dateieinlesung
  - PDF-Parsing
  - Chunking
  - Retry-Logik
  - Output-Schreiben
- Einheitliches Konfigurationsmodell fuer alle Tools einfuehren.
- API-Key ausschliesslich ueber Environment Variables laden.
- Hart codierte Secrets entfernen.
- Kodierungsprobleme bereinigen.
- Konsistente Ergebnisobjekte definieren:
  - Status
  - Metadaten
  - Fehler
  - Artefakte
- Logging verbessern.
- Fehlerbehandlung fuer ungueltige Dateien und Modellantworten robuster machen.
- Einheitliche Ordnerstruktur fuer Uploads und Ergebnisse definieren.

Ergebnis:

- Ein gemeinsames Python-Paket oder Service-Verzeichnis, in dem alle drei Tools als wiederverwendbare Funktionen laufen.

## Phase 2: Backend/API aufbauen

Ziel: Die Python-Engine ueber ein Web-Backend steuerbar machen.

Technische Richtung:

- `FastAPI` als API-Schicht.

Aufgaben:

- API-Grundstruktur anlegen.
- Endpunkte definieren:
  - Login-nahe geschuetzte Requests vorbereiten
  - Projekt anlegen
  - Datei hochladen
  - Job starten
  - Jobstatus abrufen
  - Ergebnisdateien herunterladen
- Drei Jobtypen integrieren:
  - `translation`
  - `bibliography`
  - `proofcheck`
- Hintergrundverarbeitung fuer laengere Jobs aufsetzen.
- Einfache Job-Queue fuer `v1` implementieren.
- Job-Statusmodell definieren:
  - `queued`
  - `running`
  - `done`
  - `failed`
- Standardisierte API-Responses und Fehlermeldungen einfuehren.

Ergebnis:

- Ein lokal und spaeter remote laufendes Python-Backend, das die drei Tools per API startet.

## Phase 3: Datenmodell und Infrastruktur

Ziel: Die App auf eine tragfaehige Daten- und Dateibasis stellen.

Aufgaben:

- Datenmodell fuer `v1` festlegen:
  - User
  - Workspace oder Verlag
  - Project
  - File
  - Job
  - Artifact
  - Glossary
- Postgres-Schema entwerfen.
- Storage-Konzept festlegen:
  - Originaldateien
  - Zwischendateien
  - DOCX/XLSX/JSONL-Ausgaben
- Benennungskonventionen fuer Dateien und Jobs definieren.
- Audit-Felder vorsehen:
  - erstellt von
  - erstellt am
  - letzter Statuswechsel
- Aufraeumregeln und Aufbewahrung mitdenken.

Ergebnis:

- Eine belastbare Grundlage fuer Mehrnutzerbetrieb und spaetere Erweiterungen.

## Phase 4: Next.js-Verlagsinterface v1

Ziel: Eine interne Arbeitsoberflaeche mit ND-Anmutung bauen.

Aufgaben:

- App-Grundgeruest in Next.js anlegen.
- Login integrieren.
- Geschuetzte App-Routen aufsetzen.
- Grundnavigation definieren:
  - Dashboard
  - Projekte
  - Tools
  - Dateien
  - Glossare
  - Einstellungen
- Projektansicht bauen.
- Upload-Flow bauen.
- Tool-Startmasken bauen:
  - Uebersetzung
  - Bibliography
  - Lektorat
- Statusansichten fuer laufende Jobs bauen.
- Ergebnisansichten bauen:
  - Downloadlinks
  - Metadaten
  - Fehlerstatus
- Visuelle Richtung an ND orientieren:
  - Logo
  - Typografie
  - Farbwelt
  - ruhige, editoriale Arbeitsoberflaeche

Ergebnis:

- Ein benutzbares internes Verlagsinterface fuer euch und deinen Onkel.

## Phase 5: Auth, Rollen und interne Freigabe

Ziel: Das Tool sicher gemeinsam nutzbar machen.

Aufgaben:

- Auth-Anbieter festlegen.
- Rollen fuer `v1` definieren:
  - Admin
  - Editor
  - eventuell Viewer
- Zugriff auf Projekte und Dateien absichern.
- Session-Handling und geschuetzte Downloads umsetzen.
- Erste interne Testnutzer anlegen.
- Nutzungsablaeufe mit realen Dateien pruefen.

Ergebnis:

- Ein live faehiges internes Tool mit Login.

## Phase 6: Deployment und Livegang

Ziel: Die App online veroeffentlichen und stabil betreiben.

Aufgaben:

- Deployment-Setup festlegen:
  - Frontend separat
  - Python-Backend separat
  - Datenbank
  - Storage
- Umgebungsvariablen sauber aufsetzen.
- Domains spaeter trennen:
  - `www` fuer Verlag/Shop
  - `app` fuer das interne Tool
  - optional `api` fuer Backend
- Monitoring und Error-Tracking einbauen.
- Backup-Strategie definieren.
- Interne Live-Abnahme mit echten Workflows machen.

Ergebnis:

- Ein stabiles, online erreichbares internes ND-Verlagsinterface.

## Phase 7: Produktisierung und SaaS-Vorbereitung

Ziel: Die interne App so erweitern, dass sie fuer andere Verlage oeffnungsfaehig wird.

Aufgaben:

- Mehrmandantenfaehigkeit sauber durchziehen.
- Workspace-/Mandanten-Trennung absichern.
- Rollenmodell erweitern.
- Nutzungslimits und Abrechnung vorbereiten.
- Onboarding fuer neue Verlage entwerfen.
- White-Labeling oder Branding-Optionen pruefen.
- Admin- und Support-Werkzeuge einbauen.
- API oder Integrationen fuer externe Workflows andenken.

Ergebnis:

- Eine klare Bruecke vom internen Tool zum vermarktbaren Produkt.

## Priorisierte Taskliste fuer den Start

Diese Aufgaben sollten wir als erstes abarbeiten:

1. Gemeinsame Architektur fuer die drei Python-Tools definieren.
2. Secrets und Sicherheitsprobleme bereinigen.
3. Die Skripte in wiederverwendbare Python-Module aufteilen.
4. Ein FastAPI-Backend als Startpunkt anlegen.
5. Das Datenmodell fuer Projekte, Jobs, Dateien und Artefakte definieren.
6. Das Next.js-App-Skelett mit Login und Dashboard anlegen.
7. Den ersten kompletten End-to-End-Flow fuer ein Tool live zum Laufen bringen.

## Empfohlener MVP-Schnitt

Was `v1` koennen sollte:

- Login
- 1 Verlag oder 1 Workspace
- Projekte anlegen
- Datei hochladen
- Eines der drei Tools starten
- Jobstatus sehen
- Ergebnis herunterladen

Was bewusst spaeter kommen kann:

- Shop-Anbindung
- Billing
- externe Kundenkonten
- Multi-Tenant-SaaS
- API fuer Dritte
- Browserbasierte Vollkorrektur oder In-App-Editor

## Erste konkrete Umsetzung nach dieser Roadmap

Naechster Arbeitsschritt:

- Wir starten mit Phase 1 und extrahieren aus den drei Skripten die gemeinsame Python-Architektur.

Direkt danach:

- Wir entscheiden die Zielstruktur fuer Backend und Frontend im Code.
- Anschliessend bauen wir das technische Grundgeruest fuer `v1`.

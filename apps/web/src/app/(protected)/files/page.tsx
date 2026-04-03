import Link from "next/link";

export default function FilesPage() {
  return (
    <section className="nd-card rounded-2xl p-6">
      <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-secondary)]">Dateien</p>
      <h2 className="serif-heading mt-2 text-4xl">Datei- und Artifact-Downloads</h2>
      <p className="mt-2 max-w-2xl text-sm text-[var(--color-text-secondary)]">
        In v1 laufen Upload und Download direkt im Projekt-Workspace, damit der gesamte Kontext pro Projekt zusammen
        bleibt.
      </p>
      <Link href="/projects" className="nd-button mt-5 inline-flex">
        Zu Projekten
      </Link>
    </section>
  );
}

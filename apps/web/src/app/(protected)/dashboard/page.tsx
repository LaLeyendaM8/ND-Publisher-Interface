import Link from "next/link";

const cards = [
  {
    title: "Projekte",
    body: "Projekte anlegen, Dateien sammeln und Workflows zentral steuern.",
    href: "/projects",
  },
  {
    title: "Tools",
    body: "Translation, Bibliography und Proofcheck als einheitliche Job-Pipeline.",
    href: "/tools",
  },
  {
    title: "Dateien",
    body: "Uploads und Ergebnisse mit Downloadlinks und Metadaten.",
    href: "/files",
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <section className="nd-card rounded-2xl p-6">
        <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-secondary)]">Dashboard</p>
        <h2 className="serif-heading mt-2 text-4xl">Interner ND Workflow</h2>
        <p className="mt-2 max-w-2xl text-sm text-[var(--color-text-secondary)]">
          Dieses Interface verbindet die drei Python-Tools in einer gemeinsamen Oberflaeche. Ziel fuer v1:
          Projektarbeit, Upload, Jobstart, Status und Ergebnisdownload.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {cards.map((card) => (
          <Link key={card.title} href={card.href} className="nd-card rounded-2xl p-5 transition hover:-translate-y-[2px]">
            <h3 className="serif-heading text-2xl">{card.title}</h3>
            <p className="mt-2 text-sm text-[var(--color-text-secondary)]">{card.body}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}

const tools = [
  {
    title: "translation",
    body: "Mechanischer Uebersetzungs-Run mit den bestehenden Python-Pipelines.",
  },
  {
    title: "bibliography",
    body: "Bibliography-normalisierung und Ausgabe in einheitlichem Schema.",
  },
  {
    title: "proofcheck",
    body: "Mechanisches Lektorat fuer strukturelle und formale Pruefschritte.",
  },
];

export default function ToolsPage() {
  return (
    <div className="space-y-6">
      <section className="nd-card rounded-2xl p-6">
        <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-secondary)]">Tools</p>
        <h2 className="serif-heading mt-2 text-4xl">Jobtypen in v1</h2>
        <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
          Die drei Tools sind bereits im Backend integriert. Start und Monitoring laufen auf der Projektseite.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {tools.map((tool) => (
          <article key={tool.title} className="nd-card rounded-2xl p-5">
            <h3 className="serif-heading text-2xl">{tool.title}</h3>
            <p className="mt-2 text-sm text-[var(--color-text-secondary)]">{tool.body}</p>
          </article>
        ))}
      </section>
    </div>
  );
}

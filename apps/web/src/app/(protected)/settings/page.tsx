export default function SettingsPage() {
  return (
    <section className="nd-card rounded-2xl p-6">
      <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-secondary)]">Einstellungen</p>
      <h2 className="serif-heading mt-2 text-4xl">System und Zugriff</h2>
      <div className="mt-4 space-y-3 text-sm text-[var(--color-text-secondary)]">
        <p>Dieser v1 Login ist als interner Zugang fuer ND aufgebaut.</p>
        <p>In Phase 5 ersetzen wir ihn durch Rollen (Admin/Editor/Viewer) und echtes Session-Management.</p>
      </div>
    </section>
  );
}

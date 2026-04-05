export default function SettingsPage() {
  return (
    <section className="nd-card rounded-2xl p-6">
      <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-secondary)]">Einstellungen</p>
      <h2 className="serif-heading mt-2 text-4xl">System und Zugriff</h2>
      <div className="mt-4 space-y-3 text-sm text-[var(--color-text-secondary)]">
        <p>Auth-Provider: Supabase Auth (Email/Passwort).</p>
        <p>Rollenmodell fuer v1: `admin`, `editor`, `viewer` (viewer ist read-only).</p>
        <p>Rollen koennen in Supabase ueber User-Metadata/App-Metadata gepflegt werden.</p>
      </div>
    </section>
  );
}

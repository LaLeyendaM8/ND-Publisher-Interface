import { redirect } from "next/navigation";
import { AppNav } from "@/components/app-nav";
import { LogoutButton } from "@/components/logout-button";
import { getCurrentAuth } from "@/lib/auth";

export default async function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const auth = await getCurrentAuth();
  if (!auth) {
    redirect("/login");
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="mx-auto flex w-full max-w-[1320px] items-center justify-between px-6 py-6 md:px-10">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-secondary)]">Negative Dialektik</p>
            <h1 className="serif-heading mt-2 text-4xl md:text-5xl">Publisher Interface</h1>
          </div>
          <div className="hidden text-right md:block">
            <p className="text-sm text-[var(--color-text-secondary)]">Interne ND Toolchain</p>
            <p className="text-xs text-[var(--color-text-secondary)]">
              {auth.email ?? "Unbekannt"} - {auth.role}
            </p>
          </div>
        </div>
      </header>

      <div className="mx-auto grid w-full max-w-[1320px] grid-cols-1 gap-6 px-6 py-8 md:px-10 lg:grid-cols-12">
        <aside className="nd-card rounded-2xl p-4 lg:col-span-3 xl:col-span-2">
          <AppNav />
          <div className="mt-4 border-t border-[var(--color-border)] pt-4">
            <LogoutButton />
          </div>
        </aside>

        <main className="lg:col-span-9 xl:col-span-10">{children}</main>
      </div>
    </div>
  );
}

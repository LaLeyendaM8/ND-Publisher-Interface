import { redirect } from "next/navigation";
import { LoginForm } from "@/components/login-form";
import { isAuthenticated } from "@/lib/auth";

export default async function LoginPage() {
  if (await isAuthenticated()) {
    redirect("/dashboard");
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[520px] items-center px-6 py-12">
      <section className="nd-card w-full rounded-2xl p-6 md:p-8">
        <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-secondary)]">Negative Dialektik</p>
        <h1 className="serif-heading mt-2 text-4xl">Publisher Interface</h1>
        <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
          Interne Arbeitsoberflaeche fuer Translation, Bibliography und Proofcheck. Login basiert auf Supabase Auth.
        </p>
        <LoginForm />
      </section>
    </main>
  );
}

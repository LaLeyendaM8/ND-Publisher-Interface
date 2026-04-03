"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export function LoginForm() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("Interner Zugang fuer ND Publisher Interface");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!password.trim()) return;
    setIsLoading(true);
    setMessage("Pruefe Login...");

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });

      if (!response.ok) {
        setMessage("Login fehlgeschlagen.");
        return;
      }

      setMessage("Login erfolgreich.");
      router.push("/dashboard");
      router.refresh();
    } catch {
      setMessage("Login fehlgeschlagen.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form className="mt-6 space-y-3" onSubmit={onSubmit}>
      <label className="text-sm text-[var(--color-text-secondary)]" htmlFor="password">
        Passwort
      </label>
      <input
        id="password"
        className="nd-input"
        autoComplete="current-password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />
      <button className="nd-button w-full" type="submit" disabled={isLoading}>
        {isLoading ? "Anmeldung..." : "Anmelden"}
      </button>
      <p className="text-xs text-[var(--color-text-secondary)]">{message}</p>
    </form>
  );
}

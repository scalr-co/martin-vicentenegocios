"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { BrandMark } from "@/components/ui";
import { apiFetch, extractToken } from "@/lib/api";
import { setSession } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const form = new FormData(e.currentTarget);
    const email = String(form.get("email") || "");
    const password = String(form.get("password") || "");

    try {
      const { data } = await apiFetch<Record<string, unknown>>("/auth/login", {
        method: "POST",
        auth: false,
        body: JSON.stringify({ email, password }),
      });

      const token = extractToken(data);
      if (!token) {
        throw new Error("La API no devolvió token. Avisa a tu amigo.");
      }

      const workshop =
        (data.workshop as unknown) ||
        (data as { workshop?: unknown }).workshop ||
        null;

      setSession(token, workshop);
      router.replace("/panel");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar sesión");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-full flex-col items-center justify-center overflow-hidden bg-steel px-4 py-16">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(232,93,4,0.25),transparent_55%)]" />

      <div className="relative w-full max-w-sm rounded-lg border border-white/10 bg-surface p-6 shadow-xl">
        <BrandMark className="text-xl" />
        <h1 className="mt-6 font-[family-name:var(--font-display)] text-2xl font-bold text-ink">
          Ingresar
        </h1>
        <p className="mt-2 text-sm text-muted">
          Acceso del taller. Las cuentas las dan de alta Martín y Solve.
        </p>

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <label className="block" htmlFor="email">
            <span className="text-sm font-medium">Email</span>
            <input
              id="email"
              name="email"
              type="email"
              required
              autoComplete="email"
              placeholder="taller@ejemplo.cl"
              className="mt-1 w-full rounded-md border border-line px-3 py-2.5 text-sm outline-none focus:border-brand focus-visible:ring-2 focus-visible:ring-brand/30"
            />
          </label>
          <label className="block" htmlFor="password">
            <span className="text-sm font-medium">Contraseña</span>
            <input
              id="password"
              name="password"
              type="password"
              required
              autoComplete="current-password"
              placeholder="••••••••"
              className="mt-1 w-full rounded-md border border-line px-3 py-2.5 text-sm outline-none focus:border-brand focus-visible:ring-2 focus-visible:ring-brand/30"
            />
          </label>

          {error && (
            <p role="alert" className="text-sm text-red-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-brand py-2.5 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-60"
          >
            {loading ? "Entrando…" : "Entrar al panel"}
          </button>
        </form>

        <p className="mt-4 text-center text-xs text-muted">
          <Link href="/" className="hover:text-ink">
            ← Volver a la landing
          </Link>
        </p>
      </div>
    </div>
  );
}

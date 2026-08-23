"use client";

import Link from "next/link";
import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { BrandMark } from "@/components/ui";
import { apiFetch, extractToken } from "@/lib/api";
import {
  extractSessionFromLogin,
  isAdmin,
  setSession,
} from "@/lib/auth";
import { errorMessage } from "@/lib/errors";
import { fieldClass } from "@/lib/form-styles";

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginShell />}>
      <LoginForm />
    </Suspense>
  );
}

function LoginShell({ children }: { children?: React.ReactNode }) {
  return (
    <div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center overflow-y-auto px-4 py-10"
      style={{ backgroundColor: "#12100e" }}
    >
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse at top, rgba(224,164,90,0.26), transparent 55%)",
        }}
      />
      <div
        className="relative w-full max-w-sm rounded-lg border bg-[#fffcf7] p-6 shadow-xl dark:bg-surface"
        style={{
          borderColor: "rgba(224,164,90,0.35)",
          boxShadow:
            "0 0 0 1px rgba(224,164,90,0.12), 0 22px 50px -24px rgba(224,164,90,0.45)",
        }}
      >
        <div
          className="absolute inset-x-0 top-0 h-1 rounded-t-lg"
          style={{
            background:
              "linear-gradient(90deg, #e0a45a, #f0c48a, #e0a45a)",
          }}
        />
        {children}
      </div>
    </div>
  );
}

function LoginForm() {
  const router = useRouter();
  const search = useSearchParams();
  const sessionExpired = search.get("razon") === "sesion";
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

      const { workshop, user } = extractSessionFromLogin(data);
      const sessionEmail = user?.email || email;
      const sessionRole = user?.role;
      setSession(
        token,
        sessionRole === "platform_admin" ? null : workshop,
        {
          ...user,
          email: sessionEmail,
          role: sessionRole,
        },
      );
      router.replace(isAdmin() ? "/panel/admin" : "/panel");
    } catch (err) {
      setError(errorMessage(err, "No se pudo iniciar sesión"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <LoginShell>
      <BrandMark size="lg" className="mt-1" />
      <h1 className="mt-4 font-[family-name:var(--font-display)] text-2xl font-bold text-ink">
        Ingresar
      </h1>
      <p className="mt-2 text-sm text-muted">
        Acceso del taller. Las cuentas las dan de alta Martín y Solve.
      </p>

      {sessionExpired && (
        <p
          role="status"
          className="mt-4 rounded-md border border-[color:var(--warn-line)] bg-warn-soft px-3 py-2 text-sm text-[color:var(--tone-ink)]"
        >
          Tu sesión expiró o ya no es válida. Vuelve a ingresar.
        </p>
      )}

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
            className={fieldClass}
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
            className={fieldClass}
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
          className="btn-brand tap-target w-full rounded-md py-2.5 text-sm font-semibold disabled:opacity-60"
        >
          {loading ? "Entrando…" : "Entrar al panel"}
        </button>
      </form>

      <p className="mt-4 text-center text-xs text-muted">
        <Link
          href="/"
          className="tap-target inline-flex items-center justify-center hover:text-ink"
        >
          ← Volver a la landing
        </Link>
      </p>
      <p className="mt-3 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-center text-[11px] text-muted">
        <Link href="/privacidad" className="hover:text-ink hover:underline">
          Privacidad
        </Link>
        <span aria-hidden>·</span>
        <Link href="/terminos" className="hover:text-ink hover:underline">
          Términos
        </Link>
      </p>
    </LoginShell>
  );
}

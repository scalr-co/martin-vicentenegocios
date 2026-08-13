"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth-guard";
import { OwnerGuard } from "@/components/owner-guard";
import { PanelShell } from "@/components/panel-shell";
import { errorMessage } from "@/lib/errors";
import { fieldClass } from "@/lib/form-styles";
import {
  canAddMechanic,
  createMechanic,
  getWorkshopPlan,
  listMechanics,
  type Mechanic,
} from "@/lib/mechanics";
import { mechanicLimit, planLabel } from "@/lib/plans";

export default function MecanicosPage() {
  return (
    <AuthGuard>
      <OwnerGuard>
        <MecanicosContent />
      </OwnerGuard>
    </AuthGuard>
  );
}

function MecanicosContent() {
  const [mechanics, setMechanics] = useState<Mechanic[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const plan = getWorkshopPlan();
  const limit = mechanicLimit(plan);
  const gate = useMemo(
    () => canAddMechanic(plan, mechanics),
    [plan, mechanics],
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setMechanics(await listMechanics());
      setListError(null);
    } catch (err) {
      setListError(errorMessage(err, "No se pudo cargar el equipo"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    const form = new FormData(e.currentTarget);
    try {
      await createMechanic({
        name: String(form.get("name") || ""),
        email: String(form.get("email") || ""),
        password: String(form.get("password") || ""),
      });
      await load();
      setCreateOpen(false);
      setFlash("Mecánico creado.");
      window.setTimeout(() => setFlash(null), 2800);
      e.currentTarget.reset();
    } catch (err) {
      setError(errorMessage(err, "No se pudo crear"));
    } finally {
      setSaving(false);
    }
  }

  const activeCount = mechanics.filter(
    (m) => m.role === "mechanic" && m.active,
  ).length;

  return (
    <PanelShell
      title="Mecánicos"
      subtitle={`Plan ${planLabel(plan)}${
        limit ? ` · hasta ${limit} activos` : " · sin tope de mecánicos"
      }`}
    >
      {flash && (
        <p
          role="status"
          className="mb-4 rounded-md border border-[color:var(--ok-line)] bg-ok-soft px-3 py-2 text-sm text-[color:var(--ok-ink)]"
        >
          {flash}
        </p>
      )}

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">
          {loading
            ? "Cargando…"
            : `${activeCount} activo${activeCount === 1 ? "" : "s"}${
                limit ? ` de ${limit}` : ""
              } · ${mechanics.length} en total`}
        </p>
        <button
          type="button"
          onClick={() => {
            setError(null);
            setCreateOpen(true);
          }}
          className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold"
        >
          Crear mecánico
        </button>
      </div>

      {!gate.ok && (
        <p className="mb-4 rounded-md border border-[color:var(--warn-line)] bg-warn-soft px-3 py-2 text-sm text-[color:var(--warn-ink)]">
          {gate.reason}
        </p>
      )}

      {listError && (
        <div
          role="alert"
          className="mb-4 rounded-md border border-red-200 bg-danger-soft px-3 py-3 text-sm text-red-800"
        >
          <p>{listError}</p>
          <button
            type="button"
            onClick={() => void load()}
            className="tap-target mt-2 rounded-md border border-red-300 bg-surface px-3 py-1.5 text-sm font-semibold"
          >
            Reintentar
          </button>
        </div>
      )}

      <ul className="space-y-3">
        {mechanics.map((m) => (
          <li key={m.id}>
            <Link
              href={`/panel/mecanicos/${m.id}`}
              className="card-lift block min-w-0 rounded-lg border border-line bg-surface p-4 hover:border-stone-300"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-semibold text-ink">{m.name}</p>
                  <p className="mt-0.5 truncate text-sm text-muted">{m.email}</p>
                </div>
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                    m.active
                      ? "bg-emerald-100 text-emerald-900"
                      : "bg-stone-200 text-stone-700"
                  }`}
                >
                  {m.role === "owner"
                    ? "Dueño"
                    : m.active
                      ? "Activo"
                      : "Apagado"}
                </span>
              </div>
            </Link>
          </li>
        ))}
        {!loading && !listError && mechanics.length === 0 && (
          <li className="rounded-lg border border-dashed border-line px-4 py-10 text-center text-sm text-muted">
            Aún no hay personas en el equipo. Crea el primer mecánico.
          </li>
        )}
      </ul>

      {createOpen && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-md rounded-lg border border-line bg-surface p-5 shadow-xl">
            <h2 className="font-[family-name:var(--font-display)] text-lg font-bold text-ink">
              Crear mecánico
            </h2>
            <form className="mt-4 space-y-3" onSubmit={onCreate}>
              <label className="block" htmlFor="name">
                <span className="text-sm font-medium">Nombre</span>
                <input
                  id="name"
                  name="name"
                  required
                  minLength={2}
                  className={fieldClass}
                  placeholder="Pedro Soto"
                />
              </label>
              <label className="block" htmlFor="email">
                <span className="text-sm font-medium">Email</span>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  className={fieldClass}
                  placeholder="pedro@taller.cl"
                />
              </label>
              <label className="block" htmlFor="password">
                <span className="text-sm font-medium">Contraseña temporal</span>
                <input
                  id="password"
                  name="password"
                  type="password"
                  minLength={8}
                  required
                  className={fieldClass}
                />
              </label>
              {error && (
                <p role="alert" className="text-sm text-red-700">
                  {error}
                </p>
              )}
              <div className="flex flex-col gap-2 sm:flex-row-reverse">
                <button
                  type="submit"
                  disabled={saving}
                  className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold disabled:opacity-60"
                >
                  {saving ? "Creando…" : "Crear"}
                </button>
                <button
                  type="button"
                  onClick={() => setCreateOpen(false)}
                  className="tap-target rounded-md border border-line px-4 py-2.5 text-sm font-semibold text-ink"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </PanelShell>
  );
}

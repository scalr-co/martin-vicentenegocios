"use client";

import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth-guard";
import { PanelShell } from "@/components/panel-shell";
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
      <MecanicosContent />
    </AuthGuard>
  );
}

function MecanicosContent() {
  const [mechanics, setMechanics] = useState<Mechanic[]>(() => listMechanics());
  const [createOpen, setCreateOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);

  const plan = useMemo(() => getWorkshopPlan(), [mechanics]);
  const limit = mechanicLimit(plan);
  const gate = canAddMechanic(plan);

  function refresh() {
    setMechanics(listMechanics());
  }

  function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const form = new FormData(e.currentTarget);
    try {
      createMechanic({
        name: String(form.get("name") || ""),
        email: String(form.get("email") || ""),
        phone: String(form.get("phone") || ""),
        notes: String(form.get("notes") || ""),
        password: String(form.get("password") || ""),
      });
      refresh();
      setCreateOpen(false);
      setFlash("Mecánico creado.");
      window.setTimeout(() => setFlash(null), 2800);
      e.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear");
    }
  }

  return (
    <PanelShell
      title="Mecánicos"
      subtitle={`Plan ${planLabel(plan)}${
        limit ? ` · hasta ${limit} cuentas` : " · sin tope de mecánicos"
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
          {mechanics.length} mecánico{mechanics.length === 1 ? "" : "s"}
          {limit ? ` de ${limit}` : ""} · vista previa local
        </p>
        <button
          type="button"
          disabled={!gate.ok}
          title={gate.reason}
          onClick={() => {
            setError(null);
            setCreateOpen(true);
          }}
          className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold disabled:opacity-50"
        >
          Crear mecánico
        </button>
      </div>

      {!gate.ok && (
        <p className="mb-4 rounded-md border border-[color:var(--warn-line)] bg-warn-soft px-3 py-2 text-sm text-[color:var(--warn-ink)]">
          {gate.reason}
        </p>
      )}

      <ul className="space-y-3">
        {mechanics.map((m) => (
          <li key={m.id}>
            <Link
              href={`/panel/mecanicos/${m.id}`}
              className="card-lift block min-w-0 rounded-lg border border-line bg-surface p-4 hover:border-stone-300"
            >
              <p className="font-semibold text-ink">{m.name}</p>
              <p className="mt-0.5 truncate text-sm text-muted">
                {m.email} · {m.phone || "Sin teléfono"}
              </p>
            </Link>
          </li>
        ))}
        {mechanics.length === 0 && (
          <li className="rounded-lg border border-dashed border-line px-4 py-10 text-center text-sm text-muted">
            Aún no hay mecánicos. Crea el primero.
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
              <label className="block" htmlFor="phone">
                <span className="text-sm font-medium">WhatsApp</span>
                <input
                  id="phone"
                  name="phone"
                  type="tel"
                  inputMode="numeric"
                  className={fieldClass}
                  placeholder="56912345678"
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
              <label className="block" htmlFor="notes">
                <span className="text-sm font-medium">Notas (opcional)</span>
                <input id="notes" name="notes" className={fieldClass} />
              </label>
              {error && (
                <p role="alert" className="text-sm text-red-700">
                  {error}
                </p>
              )}
              <div className="flex flex-col gap-2 sm:flex-row-reverse">
                <button
                  type="submit"
                  className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold"
                >
                  Crear
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

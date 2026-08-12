"use client";

import { FormEvent, useMemo, useState } from "react";
import { AdminGuard } from "@/components/admin-guard";
import { PanelShell } from "@/components/panel-shell";
import {
  countWorkshopAccounts,
  createWorkshopAccount,
  deleteWorkshopAccount,
  listWorkshopAccounts,
  reactivateWorkshopAccount,
  suspendWorkshopAccount,
  type WorkshopAccount,
} from "@/lib/admin-accounts";

const fieldClass =
  "mt-1 box-border block w-full min-w-0 max-w-full rounded-md border border-line bg-white px-3 py-2.5 text-sm text-stone-900 placeholder:text-stone-500 outline-none focus:border-brand focus-visible:ring-2 focus-visible:ring-brand/30";

export default function AdminPage() {
  return (
    <AdminGuard>
      <AdminContent />
    </AdminGuard>
  );
}

function AdminContent() {
  const [accounts, setAccounts] = useState<WorkshopAccount[]>(() =>
    listWorkshopAccounts(),
  );
  const [flash, setFlash] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [suspendId, setSuspendId] = useState<string | null>(null);
  const [suspendDays, setSuspendDays] = useState(7);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const counts = useMemo(() => countWorkshopAccounts(), [accounts]);

  function refresh() {
    setAccounts(listWorkshopAccounts());
  }

  function showFlash(msg: string) {
    setFlash(msg);
    window.setTimeout(() => setFlash(null), 3200);
  }

  function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const name = String(form.get("name") || "").trim();
    const ownerName = String(form.get("ownerName") || "").trim();
    const email = String(form.get("email") || "").trim();
    const phone = String(form.get("phone") || "").trim();
    const password = String(form.get("password") || "").trim();

    createWorkshopAccount({ name, ownerName, email, phone, password });
    refresh();
    setCreateOpen(false);
    showFlash(
      `Cuenta creada: “${name}”. Al entrar verá ese nombre arriba en el panel.`,
    );
    e.currentTarget.reset();
  }

  function onSuspendConfirm() {
    if (!suspendId) return;
    suspendWorkshopAccount(suspendId, suspendDays);
    refresh();
    setSuspendId(null);
    showFlash(`Cuenta suspendida por ${suspendDays} días.`);
  }

  function onDeleteConfirm() {
    if (!confirmDeleteId) return;
    deleteWorkshopAccount(confirmDeleteId);
    refresh();
    setConfirmDeleteId(null);
    showFlash("Cuenta eliminada.");
  }

  return (
    <PanelShell
      title="Administración"
      subtitle="Crear, suspender y eliminar cuentas de talleres. Solo ustedes ven esto."
    >
      {flash && (
        <div
          role="status"
          className="mb-4 rounded-md border border-[color:var(--ok-line)] bg-ok-soft px-4 py-3 text-sm text-[color:var(--tone-ink)]"
        >
          {flash}
        </div>
      )}

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <Stat label="Cuentas totales" value={counts.total} />
        <Stat label="Activas" value={counts.active} tone="ok" />
        <Stat label="Suspendidas" value={counts.suspended} tone="warn" />
      </div>

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">
          Vista previa local — cuando la API de admin esté lista, se conecta aquí.
        </p>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold"
        >
          Crear cuenta
        </button>
      </div>

      <ul className="space-y-3">
        {accounts.map((account) => (
          <li
            key={account.id}
            className="rounded-lg border border-line bg-surface p-4"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-[family-name:var(--font-display)] text-lg font-bold text-ink">
                  {account.name}
                </p>
                <p className="mt-0.5 text-sm text-muted">
                  {account.ownerName} · {account.email}
                </p>
                <p className="mt-0.5 text-xs text-muted">
                  WhatsApp {account.phone} · Alta {account.createdAt}
                  {account.status === "suspended" && account.suspendedUntil
                    ? ` · Suspendida hasta ${account.suspendedUntil}`
                    : ""}
                </p>
              </div>
              <StatusPill status={account.status} />
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {account.status === "active" ? (
                <button
                  type="button"
                  onClick={() => {
                    setSuspendId(account.id);
                    setSuspendDays(7);
                  }}
                  className="rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink hover:bg-chip"
                >
                  Suspender
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    reactivateWorkshopAccount(account.id);
                    refresh();
                    showFlash("Cuenta reactivada.");
                  }}
                  className="rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink hover:bg-chip"
                >
                  Reactivar
                </button>
              )}
              <button
                type="button"
                onClick={() => setConfirmDeleteId(account.id)}
                className="rounded-md border border-red-200 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50"
              >
                Eliminar
              </button>
            </div>
          </li>
        ))}
        {accounts.length === 0 && (
          <li className="rounded-lg border border-dashed border-line px-4 py-10 text-center text-sm text-muted">
            No hay cuentas todavía. Crea la primera.
          </li>
        )}
      </ul>

      {createOpen && (
        <Modal
          title="Crear cuenta de taller"
          onClose={() => setCreateOpen(false)}
        >
          <p className="text-sm text-muted">
            El nombre del taller (ej. “Taller Juanito”) es el que verá arriba al
            entrar al panel.
          </p>
          <form className="mt-4 space-y-3" onSubmit={onCreate}>
            <label className="block min-w-0" htmlFor="name">
              <span className="text-sm font-medium">Nombre del taller</span>
              <input
                id="name"
                name="name"
                required
                minLength={2}
                className={fieldClass}
                placeholder="Taller Juanito"
              />
            </label>
            <label className="block min-w-0" htmlFor="ownerName">
              <span className="text-sm font-medium">Dueño / contacto</span>
              <input
                id="ownerName"
                name="ownerName"
                required
                className={fieldClass}
                placeholder="Juan Pérez"
              />
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block min-w-0" htmlFor="email">
                <span className="text-sm font-medium">Email de acceso</span>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  className={fieldClass}
                  placeholder="juanito@taller.cl"
                />
              </label>
              <label className="block min-w-0" htmlFor="phone">
                <span className="text-sm font-medium">WhatsApp taller</span>
                <input
                  id="phone"
                  name="phone"
                  required
                  className={fieldClass}
                  placeholder="56912345678"
                />
              </label>
            </div>
            <label className="block min-w-0" htmlFor="password">
              <span className="text-sm font-medium">Contraseña temporal</span>
              <input
                id="password"
                name="password"
                type="password"
                required
                minLength={8}
                className={fieldClass}
                placeholder="Mínimo 8 caracteres"
              />
            </label>
            <div className="flex flex-col gap-2 pt-2 sm:flex-row-reverse">
              <button
                type="submit"
                className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold"
              >
                Crear cuenta
              </button>
              <button
                type="button"
                onClick={() => setCreateOpen(false)}
                className="tap-target rounded-md border border-line bg-white px-4 py-2.5 text-sm font-semibold text-stone-900"
              >
                Cancelar
              </button>
            </div>
          </form>
        </Modal>
      )}

      {suspendId && (
        <Modal title="Suspender cuenta" onClose={() => setSuspendId(null)}>
          <p className="text-sm text-muted">
            El taller no podrá entrar hasta que termine la suspensión o lo
            reactives.
          </p>
          <label className="mt-4 block" htmlFor="suspendDays">
            <span className="text-sm font-medium">Días de suspensión</span>
            <select
              id="suspendDays"
              className={fieldClass}
              value={suspendDays}
              onChange={(e) => setSuspendDays(Number(e.target.value))}
            >
              <option value={7}>7 días</option>
              <option value={15}>15 días</option>
              <option value={30}>30 días</option>
              <option value={90}>90 días</option>
            </select>
          </label>
          <div className="mt-5 flex flex-col gap-2 sm:flex-row-reverse">
            <button
              type="button"
              onClick={onSuspendConfirm}
              className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold"
            >
              Confirmar suspensión
            </button>
            <button
              type="button"
              onClick={() => setSuspendId(null)}
              className="tap-target rounded-md border border-line bg-white px-4 py-2.5 text-sm font-semibold text-stone-900"
            >
              Cancelar
            </button>
          </div>
        </Modal>
      )}

      {confirmDeleteId && (
        <Modal title="Eliminar cuenta" onClose={() => setConfirmDeleteId(null)}>
          <p className="text-sm text-muted">
            Esto quita el acceso del taller. En la API debería ser irreversible
            o soft-delete; por ahora es solo la vista.
          </p>
          <div className="mt-5 flex flex-col gap-2 sm:flex-row-reverse">
            <button
              type="button"
              onClick={onDeleteConfirm}
              className="tap-target rounded-md bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800"
            >
              Sí, eliminar
            </button>
            <button
              type="button"
              onClick={() => setConfirmDeleteId(null)}
              className="tap-target rounded-md border border-line bg-white px-4 py-2.5 text-sm font-semibold text-stone-900"
            >
              Cancelar
            </button>
          </div>
        </Modal>
      )}
    </PanelShell>
  );
}

function Stat({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: number;
  tone?: "neutral" | "ok" | "warn";
}) {
  const toneClass =
    tone === "warn"
      ? "border-[color:var(--warn-line)] bg-warn-soft"
      : tone === "ok"
        ? "border-[color:var(--ok-line)] bg-ok-soft"
        : "border-line bg-surface";
  const labelClass =
    tone === "neutral" ? "text-muted" : "text-[color:var(--tone-ink)]";
  const valueClass =
    tone === "neutral" ? "text-ink" : "text-[color:var(--tone-ink)]";

  return (
    <div className={`rounded-lg border px-4 py-3 ${toneClass}`}>
      <p className={`text-xs font-medium ${labelClass}`}>{label}</p>
      <p
        className={`mt-1 font-[family-name:var(--font-display)] text-2xl font-bold ${valueClass}`}
      >
        {value}
      </p>
    </div>
  );
}

function StatusPill({ status }: { status: WorkshopAccount["status"] }) {
  if (status === "suspended") {
    return (
      <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-900">
        Suspendida
      </span>
    );
  }
  return (
    <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-900">
      Activa
    </span>
  );
}

function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center"
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-md rounded-lg border border-line bg-surface p-5 shadow-xl">
        <div className="flex items-start justify-between gap-3">
          <h2 className="font-[family-name:var(--font-display)] text-lg font-bold text-ink">
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-sm text-muted hover:text-ink"
          >
            Cerrar
          </button>
        </div>
        <div className="mt-2">{children}</div>
      </div>
    </div>
  );
}

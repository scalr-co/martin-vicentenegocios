"use client";

import { FormEvent, useMemo, useState } from "react";
import { AdminGuard } from "@/components/admin-guard";
import { PanelShell } from "@/components/panel-shell";
import { fieldClass } from "@/lib/form-styles";
import {
  countWorkshopAccounts,
  createWorkshopAccount,
  deleteWorkshopAccount,
  getWorkshopAccount,
  listWorkshopAccounts,
  reactivateWorkshopAccount,
  suspendWorkshopAccount,
  type SuspendOption,
  type WorkshopAccount,
} from "@/lib/admin-accounts";
import {
  planFeatures,
  planLabel,
  type WorkshopPlan,
} from "@/lib/plans";

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
  const [createPlan, setCreatePlan] = useState<WorkshopPlan>("basico");
  const [detailId, setDetailId] = useState<string | null>(null);
  const [suspendId, setSuspendId] = useState<string | null>(null);
  const [suspendOption, setSuspendOption] = useState<SuspendOption>(7);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const counts = useMemo(() => countWorkshopAccounts(), [accounts]);
  const detail = detailId ? getWorkshopAccount(detailId) : null;

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
    const plan = (String(form.get("plan") || "basico") === "plus"
      ? "plus"
      : "basico") as WorkshopPlan;

    createWorkshopAccount({ name, ownerName, email, phone, password, plan });
    refresh();
    setCreateOpen(false);
    setCreatePlan("basico");
    showFlash(`Cuenta creada: “${name}” · Plan ${planLabel(plan)}`);
    e.currentTarget.reset();
  }

  function onSuspendConfirm() {
    if (!suspendId) return;
    suspendWorkshopAccount(suspendId, suspendOption);
    refresh();
    setSuspendId(null);
    showFlash(
      suspendOption === "indefinite"
        ? "Cuenta suspendida hasta que la reactiven."
        : `Cuenta suspendida por ${suspendOption} días.`,
    );
  }

  function onDeleteConfirm() {
    if (!confirmDeleteId) return;
    deleteWorkshopAccount(confirmDeleteId);
    refresh();
    if (detailId === confirmDeleteId) setDetailId(null);
    setConfirmDeleteId(null);
    showFlash("Cuenta eliminada.");
  }

  if (detail) {
    return (
      <PanelShell
        title={detail.name}
        subtitle="Detalle del taller (vista previa local)"
      >
        {flash && <Flash msg={flash} />}
        <button
          type="button"
          onClick={() => setDetailId(null)}
          className="tap-target mb-4 inline-flex items-center text-sm text-muted hover:text-ink"
        >
          ← Volver a talleres
        </button>

        <div className="rounded-lg border border-line bg-surface p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                Plan {planLabel(detail.plan)}
              </p>
              <p className="mt-1 font-[family-name:var(--font-display)] text-2xl font-bold text-ink">
                {detail.name}
              </p>
            </div>
            <StatusPill status={detail.status} />
          </div>

          <dl className="mt-6 grid gap-4 sm:grid-cols-2">
            <Info label="Dueño / contacto" value={detail.ownerName} />
            <Info label="Email de acceso" value={detail.email} />
            <Info label="WhatsApp" value={detail.phone} />
            <Info label="Alta" value={detail.createdAt} />
            <Info
              label="Suspensión"
              value={
                detail.status !== "suspended"
                  ? "—"
                  : detail.suspendIndefinite
                    ? "Hasta que la reactivemos"
                    : detail.suspendedUntil
                      ? `Hasta ${detail.suspendedUntil}`
                      : "—"
              }
            />
          </dl>

          <div className="mt-6">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">
              Ventajas del plan
            </p>
            <ul className="mt-2 space-y-1.5">
              {planFeatures(detail.plan).map((f) => (
                <li key={f} className="text-sm text-ink">
                  · {f}
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-6 flex flex-wrap gap-2 border-t border-line pt-5">
            {detail.status === "active" ? (
              <button
                type="button"
                onClick={() => {
                  setSuspendId(detail.id);
                  setSuspendOption(7);
                }}
                className="tap-target rounded-md bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800"
              >
                Suspender cuenta
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  reactivateWorkshopAccount(detail.id);
                  refresh();
                  showFlash("Cuenta reactivada.");
                }}
                className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold"
              >
                Reactivar
              </button>
            )}
            <button
              type="button"
              onClick={() => setConfirmDeleteId(detail.id)}
              className="tap-target rounded-md border border-red-300 px-4 py-2.5 text-sm font-semibold text-red-700 hover:bg-red-50"
            >
              Eliminar
            </button>
          </div>
        </div>

        {suspendId && (
          <SuspendModal
            option={suspendOption}
            setOption={setSuspendOption}
            onConfirm={onSuspendConfirm}
            onClose={() => setSuspendId(null)}
          />
        )}
        {confirmDeleteId && (
          <DeleteModal
            onConfirm={onDeleteConfirm}
            onClose={() => setConfirmDeleteId(null)}
          />
        )}
      </PanelShell>
    );
  }

  return (
    <PanelShell
      title="Administración"
      subtitle="Talleres del SaaS — vista previa hasta conectar la API"
    >
      {flash && <Flash msg={flash} />}

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <Stat label="Cuentas totales" value={counts.total} />
        <Stat label="Activas" value={counts.active} tone="ok" />
        <Stat label="Suspendidas" value={counts.suspended} tone="warn" />
      </div>

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">
          Lista de talleres registrados. Toca uno para ver el detalle.
        </p>
        <button
          type="button"
          onClick={() => {
            setCreatePlan("basico");
            setCreateOpen(true);
          }}
          className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold"
        >
          Crear cuenta de taller
        </button>
      </div>

      <ul className="space-y-3">
        {accounts.map((account) => (
          <li
            key={account.id}
            className="rounded-lg border border-line bg-surface p-4"
          >
            <button
              type="button"
              onClick={() => setDetailId(account.id)}
              className="w-full min-w-0 text-left"
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
                    Plan {planLabel(account.plan)} · WhatsApp {account.phone}
                    {account.status === "suspended"
                      ? account.suspendIndefinite
                        ? " · Suspendida (manual)"
                        : account.suspendedUntil
                          ? ` · Hasta ${account.suspendedUntil}`
                          : ""
                      : ""}
                  </p>
                </div>
                <StatusPill status={account.status} />
              </div>
            </button>

            <div className="mt-4 flex flex-wrap gap-2 border-t border-line pt-3">
              <button
                type="button"
                onClick={() => setDetailId(account.id)}
                className="tap-target rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink hover:bg-chip"
              >
                Ver información
              </button>
              {account.status === "active" ? (
                <button
                  type="button"
                  onClick={() => {
                    setSuspendId(account.id);
                    setSuspendOption(7);
                  }}
                  className="tap-target rounded-md bg-red-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-800"
                >
                  Suspender cuenta
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    reactivateWorkshopAccount(account.id);
                    refresh();
                    showFlash("Cuenta reactivada.");
                  }}
                  className="tap-target rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink hover:bg-chip"
                >
                  Reactivar
                </button>
              )}
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
        <Modal title="Crear cuenta de taller" onClose={() => setCreateOpen(false)}>
          <form className="mt-2 space-y-3" onSubmit={onCreate}>
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
                  type="tel"
                  inputMode="numeric"
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

            <fieldset className="rounded-lg border border-line p-3">
              <legend className="px-1 text-sm font-medium text-ink">
                Plan
              </legend>
              <div className="mt-1 flex flex-wrap gap-2">
                {(["basico", "plus"] as const).map((p) => (
                  <label
                    key={p}
                    className={`tap-target flex cursor-pointer items-center rounded-md border px-3 py-2 text-sm ${
                      createPlan === p
                        ? "border-brand bg-chip font-semibold text-ink"
                        : "border-line text-muted"
                    }`}
                  >
                    <input
                      type="radio"
                      name="plan"
                      value={p}
                      checked={createPlan === p}
                      onChange={() => setCreatePlan(p)}
                      className="sr-only"
                    />
                    {planLabel(p)}
                  </label>
                ))}
              </div>
              <ul className="mt-3 max-h-40 space-y-1 overflow-y-auto text-xs text-muted">
                {planFeatures(createPlan).map((f) => (
                  <li key={f}>· {f}</li>
                ))}
              </ul>
            </fieldset>

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
                className="tap-target rounded-md border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink"
              >
                Cancelar
              </button>
            </div>
          </form>
        </Modal>
      )}

      {suspendId && (
        <SuspendModal
          option={suspendOption}
          setOption={setSuspendOption}
          onConfirm={onSuspendConfirm}
          onClose={() => setSuspendId(null)}
        />
      )}
      {confirmDeleteId && (
        <DeleteModal
          onConfirm={onDeleteConfirm}
          onClose={() => setConfirmDeleteId(null)}
        />
      )}
    </PanelShell>
  );
}

function Flash({ msg }: { msg: string }) {
  return (
    <div
      role="status"
      className="mb-4 rounded-md border border-[color:var(--ok-line)] bg-ok-soft px-4 py-3 text-sm text-[color:var(--ok-ink)]"
    >
      {msg}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-muted">
        {label}
      </dt>
      <dd className="mt-1 text-sm text-ink">{value}</dd>
    </div>
  );
}

function SuspendModal({
  option,
  setOption,
  onConfirm,
  onClose,
}: {
  option: SuspendOption;
  setOption: (o: SuspendOption) => void;
  onConfirm: () => void;
  onClose: () => void;
}) {
  const options: { value: SuspendOption; label: string }[] = [
    { value: 7, label: "7 días" },
    { value: 14, label: "14 días" },
    { value: 21, label: "21 días" },
    { value: 31, label: "31 días" },
    { value: "indefinite", label: "Hasta que nosotros lo cambiemos" },
  ];

  return (
    <Modal title="Suspender cuenta" onClose={onClose}>
      <p className="text-sm text-muted">
        El taller no podrá entrar hasta que termine la suspensión o lo
        reactives.
      </p>
      <label className="mt-4 block" htmlFor="suspendOption">
        <span className="text-sm font-medium">Periodo</span>
        <select
          id="suspendOption"
          className={fieldClass}
          value={String(option)}
          onChange={(e) => {
            const v = e.target.value;
            setOption(
              v === "indefinite" ? "indefinite" : (Number(v) as SuspendOption),
            );
          }}
        >
          {options.map((o) => (
            <option key={String(o.value)} value={String(o.value)}>
              {o.label}
            </option>
          ))}
        </select>
      </label>
      <div className="mt-5 flex flex-col gap-2 sm:flex-row-reverse">
        <button
          type="button"
          onClick={onConfirm}
          className="tap-target rounded-md bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800"
        >
          Confirmar suspensión
        </button>
        <button
          type="button"
          onClick={onClose}
          className="tap-target rounded-md border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink"
        >
          Cancelar
        </button>
      </div>
    </Modal>
  );
}

function DeleteModal({
  onConfirm,
  onClose,
}: {
  onConfirm: () => void;
  onClose: () => void;
}) {
  return (
    <Modal title="Eliminar cuenta" onClose={onClose}>
      <p className="text-sm text-muted">
        Esto quita el acceso del taller. En la API debería ser irreversible o
        soft-delete; por ahora es solo la vista.
      </p>
      <div className="mt-5 flex flex-col gap-2 sm:flex-row-reverse">
        <button
          type="button"
          onClick={onConfirm}
          className="tap-target rounded-md bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800"
        >
          Eliminar
        </button>
        <button
          type="button"
          onClick={onClose}
          className="tap-target rounded-md border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink"
        >
          Cancelar
        </button>
      </div>
    </Modal>
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
    tone === "warn"
      ? "text-[color:var(--warn-ink)]"
      : tone === "ok"
        ? "text-[color:var(--ok-ink)]"
        : "text-muted";
  const valueClass =
    tone === "warn"
      ? "text-[color:var(--warn-ink)]"
      : tone === "ok"
        ? "text-[color:var(--ok-ink)]"
        : "text-ink";

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
      <span className="rounded-full bg-yellow-100 px-2.5 py-1 text-xs font-medium text-yellow-900">
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
      <div className="max-h-[90dvh] w-full max-w-md overflow-y-auto rounded-lg border border-line bg-surface p-5 shadow-xl">
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

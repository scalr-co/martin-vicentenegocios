"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { AdminGuard } from "@/components/admin-guard";
import { PanelShell } from "@/components/panel-shell";
import { errorMessage } from "@/lib/errors";
import { fieldClass } from "@/lib/form-styles";
import {
  countWorkshopAccounts,
  createWorkshopAccount,
  deleteWorkshopAccount,
  getWorkshopAccount,
  listWorkshopAccounts,
  reactivateWorkshopAccount,
  restoreWorkshopAccount,
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
  const [accounts, setAccounts] = useState<WorkshopAccount[]>([]);
  const [archived, setArchived] = useState(false);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [createPlan, setCreatePlan] = useState<WorkshopPlan>("basico");
  const [saving, setSaving] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [detail, setDetail] = useState<WorkshopAccount | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [suspendId, setSuspendId] = useState<string | null>(null);
  const [suspendOption, setSuspendOption] = useState<SuspendOption>(7);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const counts = useMemo(() => countWorkshopAccounts(accounts), [accounts]);

  const showFlash = useCallback((msg: string) => {
    setFlash(msg);
    window.setTimeout(() => setFlash(null), 3200);
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setAccounts(await listWorkshopAccounts({ archived }));
      setListError(null);
    } catch (err) {
      setListError(errorMessage(err, "No se pudieron cargar los talleres"));
    } finally {
      setLoading(false);
    }
  }, [archived]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!detailId) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setDetailLoading(true);
    void getWorkshopAccount(detailId)
      .then((w) => {
        if (!cancelled) setDetail(w);
      })
      .catch((err) => {
        if (!cancelled) {
          setActionError(errorMessage(err, "No se pudo cargar el detalle"));
          setDetail(null);
        }
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [detailId]);

  async function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setActionError(null);
    setSaving(true);
    const form = new FormData(e.currentTarget);
    const workshopName = String(form.get("workshopName") || "").trim();
    const ownerName = String(form.get("ownerName") || "").trim();
    const email = String(form.get("email") || "").trim();
    const workshopPhone = String(form.get("workshopPhone") || "").trim();
    const password = String(form.get("password") || "").trim();
    const plan = (String(form.get("plan") || "basico") === "plus"
      ? "plus"
      : "basico") as WorkshopPlan;

    try {
      await createWorkshopAccount({
        workshopName,
        workshopPhone,
        ownerName,
        email,
        password,
        plan,
      });
      setCreateOpen(false);
      setCreatePlan("basico");
      showFlash(`Cuenta creada: “${workshopName}” · Plan ${planLabel(plan)}`);
      e.currentTarget.reset();
      await refresh();
    } catch (err) {
      setActionError(errorMessage(err, "No se pudo crear la cuenta"));
    } finally {
      setSaving(false);
    }
  }

  async function onSuspendConfirm() {
    if (!suspendId) return;
    const id = suspendId;
    setActionError(null);
    setSaving(true);
    try {
      await suspendWorkshopAccount(id, suspendOption);
      setSuspendId(null);
      showFlash(
        suspendOption === "indefinite"
          ? "Cuenta suspendida hasta que la reactiven."
          : `Cuenta suspendida por ${suspendOption} días.`,
      );
      await refresh();
      if (detailId === id) {
        setDetail(await getWorkshopAccount(id));
      }
    } catch (err) {
      setActionError(errorMessage(err, "No se pudo suspender"));
    } finally {
      setSaving(false);
    }
  }

  async function onReactivate(id: string) {
    setActionError(null);
    setSaving(true);
    try {
      await reactivateWorkshopAccount(id);
      showFlash("Cuenta reactivada.");
      await refresh();
      if (detailId === id) setDetail(await getWorkshopAccount(id));
    } catch (err) {
      setActionError(errorMessage(err, "No se pudo reactivar"));
    } finally {
      setSaving(false);
    }
  }

  async function onDeleteConfirm() {
    if (!confirmDeleteId) return;
    setActionError(null);
    setSaving(true);
    try {
      await deleteWorkshopAccount(confirmDeleteId);
      setConfirmDeleteId(null);
      if (detailId === confirmDeleteId) setDetailId(null);
      showFlash("Taller dado de baja.");
      await refresh();
    } catch (err) {
      setActionError(errorMessage(err, "No se pudo dar de baja"));
    } finally {
      setSaving(false);
    }
  }

  async function onRestore(id: string) {
    setActionError(null);
    setSaving(true);
    try {
      await restoreWorkshopAccount(id);
      showFlash("Taller restaurado.");
      await refresh();
      if (detailId === id) setDetail(await getWorkshopAccount(id));
    } catch (err) {
      setActionError(errorMessage(err, "No se pudo restaurar"));
    } finally {
      setSaving(false);
    }
  }

  if (detailId) {
    return (
      <PanelShell
        title={detail?.name || "Taller"}
        subtitle="Detalle del taller"
      >
        {flash && <Flash msg={flash} />}
        {actionError && (
          <p role="alert" className="mb-4 text-sm text-red-700">
            {actionError}
          </p>
        )}
        <button
          type="button"
          onClick={() => setDetailId(null)}
          className="tap-target mb-4 inline-flex items-center text-sm text-muted hover:text-ink"
        >
          ← Volver a talleres
        </button>

        {detailLoading && (
          <p className="text-sm text-muted">Cargando ficha…</p>
        )}

        {detail && !detailLoading && (
          <div className="rounded-lg border border-line bg-surface p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                  Plan {planLabel(detail.plan === "plus" ? "plus" : "basico")}
                </p>
                <p className="mt-1 font-[family-name:var(--font-display)] text-2xl font-bold text-ink">
                  {detail.name}
                </p>
              </div>
              <StatusPill status={detail.status} />
            </div>

            <dl className="mt-6 grid gap-4 sm:grid-cols-2">
              <Info
                label="Email dueño"
                value={detail.ownerEmail || "—"}
              />
              <Info label="WhatsApp" value={detail.phone} />
              <Info
                label="Puede entrar hoy"
                value={detail.active ? "Sí" : "No"}
              />
              <Info label="Alta" value={detail.createdAt || "—"} />
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
              {detail.stats && (
                <>
                  <Info
                    label="Órdenes (abiertas / total)"
                    value={`${detail.stats.ordersOpen ?? 0} / ${detail.stats.ordersTotal ?? 0}`}
                  />
                  <Info
                    label="Avisos sin enviar"
                    value={String(detail.stats.noticesPending ?? 0)}
                  />
                  <Info
                    label="Usuarios activos"
                    value={String(detail.stats.usersActive ?? 0)}
                  />
                  <Info
                    label="Última actividad"
                    value={detail.stats.lastActivityAt || "—"}
                  />
                </>
              )}
            </dl>

            <div className="mt-6">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                Ventajas del plan
              </p>
              <ul className="mt-2 space-y-1.5">
                {planFeatures(
                  detail.plan === "plus" ? "plus" : "basico",
                ).map((f) => (
                  <li key={f} className="text-sm text-ink">
                    · {f}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-6 flex flex-wrap gap-2 border-t border-line pt-5">
              {detail.status === "deleted" ? (
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => void onRestore(detail.id)}
                  className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold disabled:opacity-60"
                >
                  Restaurar
                </button>
              ) : detail.status === "active" ? (
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
                  disabled={saving}
                  onClick={() => void onReactivate(detail.id)}
                  className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold disabled:opacity-60"
                >
                  Reactivar
                </button>
              )}
              {detail.status !== "deleted" && (
                <button
                  type="button"
                  onClick={() => setConfirmDeleteId(detail.id)}
                  className="tap-target rounded-md border border-red-300 px-4 py-2.5 text-sm font-semibold text-red-700 hover:bg-red-50"
                >
                  Dar de baja
                </button>
              )}
            </div>
          </div>
        )}

        {suspendId && (
          <SuspendModal
            option={suspendOption}
            setOption={setSuspendOption}
            saving={saving}
            onConfirm={() => void onSuspendConfirm()}
            onClose={() => setSuspendId(null)}
          />
        )}
        {confirmDeleteId && (
          <DeleteModal
            saving={saving}
            onConfirm={() => void onDeleteConfirm()}
            onClose={() => setConfirmDeleteId(null)}
          />
        )}
      </PanelShell>
    );
  }

  return (
    <PanelShell
      title="Talleres del SaaS"
      subtitle="Cuentas registradas en la API"
      headerAction={
        <button
          type="button"
          onClick={() => {
            setActionError(null);
            setCreatePlan("basico");
            setCreateOpen(true);
          }}
          className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold"
        >
          Crear cuenta de taller
        </button>
      }
    >
      {flash && <Flash msg={flash} />}
      {actionError && (
        <p role="alert" className="mb-4 text-sm text-red-700">
          {actionError}
        </p>
      )}

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <Stat label="Cuentas totales" value={counts.total} />
        <Stat label="Activas" value={counts.active} tone="ok" />
        <Stat label="Suspendidas" value={counts.suspended} tone="warn" />
      </div>

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">
          {loading
            ? "Cargando talleres…"
            : "Lista de talleres. Toca uno para ver el detalle."}
        </p>
        <button
          type="button"
          onClick={() => setArchived((v) => !v)}
          className={`tap-target rounded-md px-3 py-1.5 text-xs font-medium ${
            archived
              ? "bg-brand text-brand-ink"
              : "border border-line text-ink hover:bg-chip"
          }`}
        >
          {archived ? "Viendo dados de baja" : "Ver dados de baja"}
        </button>
      </div>

      {listError && (
        <div
          role="alert"
          className="mb-4 rounded-md border border-red-200 bg-danger-soft px-3 py-3 text-sm text-red-800"
        >
          <p>{listError}</p>
          <button
            type="button"
            onClick={() => void refresh()}
            className="tap-target mt-2 rounded-md border border-red-300 bg-surface px-3 py-1.5 text-sm font-semibold"
          >
            Reintentar
          </button>
        </div>
      )}

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
                    {account.ownerEmail || "Sin email dueño"}
                    {typeof account.ordersCount === "number"
                      ? ` · ${account.ordersCount} órdenes`
                      : ""}
                  </p>
                  <p className="mt-0.5 text-xs text-muted">
                    Plan{" "}
                    {planLabel(account.plan === "plus" ? "plus" : "basico")} ·
                    WhatsApp {account.phone}
                    {account.status === "suspended"
                      ? account.suspendIndefinite
                        ? " · Suspendida (manual)"
                        : account.suspendedUntil
                          ? ` · Hasta ${account.suspendedUntil}`
                          : ""
                      : ""}
                    {!account.active && account.status === "active"
                      ? " · Sin acceso hoy"
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
              {account.status === "deleted" ? (
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => void onRestore(account.id)}
                  className="tap-target rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink hover:bg-chip disabled:opacity-60"
                >
                  Restaurar
                </button>
              ) : account.status === "active" ? (
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
                  disabled={saving}
                  onClick={() => void onReactivate(account.id)}
                  className="tap-target rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink hover:bg-chip disabled:opacity-60"
                >
                  Reactivar
                </button>
              )}
            </div>
          </li>
        ))}
        {!loading && !listError && accounts.length === 0 && (
          <li className="rounded-lg border border-dashed border-line px-4 py-10 text-center text-sm text-muted">
            {archived
              ? "No hay talleres dados de baja."
              : "No hay cuentas todavía. Crea la primera."}
          </li>
        )}
      </ul>

      {createOpen && (
        <Modal
          title="Crear cuenta de taller"
          onClose={() => setCreateOpen(false)}
        >
          <form className="mt-2 space-y-3" onSubmit={onCreate}>
            <label className="block min-w-0" htmlFor="workshopName">
              <span className="text-sm font-medium">Nombre del taller</span>
              <input
                id="workshopName"
                name="workshopName"
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
                minLength={2}
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
              <label className="block min-w-0" htmlFor="workshopPhone">
                <span className="text-sm font-medium">WhatsApp taller</span>
                <input
                  id="workshopPhone"
                  name="workshopPhone"
                  type="tel"
                  inputMode="numeric"
                  required
                  minLength={8}
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
              <legend className="px-1 text-sm font-medium text-ink">Plan</legend>
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

            {actionError && (
              <p role="alert" className="text-sm text-red-700">
                {actionError}
              </p>
            )}

            <div className="flex flex-col gap-2 pt-2 sm:flex-row-reverse">
              <button
                type="submit"
                disabled={saving}
                className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold disabled:opacity-60"
              >
                {saving ? "Creando…" : "Crear cuenta"}
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
          saving={saving}
          onConfirm={() => void onSuspendConfirm()}
          onClose={() => setSuspendId(null)}
        />
      )}
      {confirmDeleteId && (
        <DeleteModal
          saving={saving}
          onConfirm={() => void onDeleteConfirm()}
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
  saving,
  onConfirm,
  onClose,
}: {
  option: SuspendOption;
  setOption: (o: SuspendOption) => void;
  saving: boolean;
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
          disabled={saving}
          onClick={onConfirm}
          className="tap-target rounded-md bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800 disabled:opacity-60"
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
  saving,
  onConfirm,
  onClose,
}: {
  saving: boolean;
  onConfirm: () => void;
  onClose: () => void;
}) {
  return (
    <Modal title="Dar de baja" onClose={onClose}>
      <p className="text-sm text-muted">
        El taller queda fuera (soft-delete). Se puede restaurar después.
      </p>
      <div className="mt-5 flex flex-col gap-2 sm:flex-row-reverse">
        <button
          type="button"
          disabled={saving}
          onClick={onConfirm}
          className="tap-target rounded-md bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800 disabled:opacity-60"
        >
          Dar de baja
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
  if (status === "deleted") {
    return (
      <span className="rounded-full bg-stone-200 px-2.5 py-1 text-xs font-medium text-stone-700">
        Baja
      </span>
    );
  }
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
        {children}
      </div>
    </div>
  );
}

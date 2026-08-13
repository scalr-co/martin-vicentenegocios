"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import {
  PanelShell,
  useLeaveBlock,
  useLeaveGuard,
} from "@/components/panel-shell";
import { StatusBadge } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { formatDateCl } from "@/lib/date";
import { errorMessage } from "@/lib/errors";
import { fieldClass } from "@/lib/form-styles";
import {
  buildWhatsAppLink,
  extractNotificationDraft,
  formatVehicleOrItem,
  isNotificationSent,
  statusLabel,
  type ApiOrder,
} from "@/lib/types";

const ALL_STATUSES = [
  "recibido",
  "en_diagnostico",
  "esperando_aprobacion",
  "en_reparacion",
  "esperando_repuesto",
  "listo",
  "entregado",
];

function normalizeOrder(data: ApiOrder): ApiOrder {
  const notice = data.latestNotification ?? data.notification ?? null;
  return {
    ...data,
    vehicleOrItem:
      data.vehicleOrItem ||
      formatVehicleOrItem(data.vehicle ?? null, "Sin vehículo"),
    latestNotification: notice,
    notification: data.notification ?? notice,
  };
}

export default function OrdenDetailPage() {
  return (
    <AuthGuard>
      <OrdenDetailLoader />
    </AuthGuard>
  );
}

function OrdenDetailLoader() {
  const params = useParams<{ id: string }>();
  const [order, setOrder] = useState<ApiOrder | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draftMessage, setDraftMessage] = useState("");
  const [draftPhone, setDraftPhone] = useState("");
  const [notificationId, setNotificationId] = useState<string | null>(null);
  const [messageSent, setMessageSent] = useState(false);

  function applyDraftFrom(payload: unknown, fallbackPhone?: string) {
    const draft = extractNotificationDraft(payload);
    if (draft?.message) setDraftMessage(draft.message);
    if (draft?.toPhone) setDraftPhone(draft.toPhone);
    else if (fallbackPhone) setDraftPhone(fallbackPhone);
    if (draft?.id) setNotificationId(draft.id);
    if (draft?.status !== undefined) {
      setMessageSent(isNotificationSent(draft.status));
    }
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const { data } = await apiFetch<ApiOrder>(`/orders/${params.id}`);
        if (cancelled) return;
        const normalized = normalizeOrder(data);
        setOrder(normalized);
        applyDraftFrom(normalized, normalized.client?.phone);
        setError(null);
      } catch (err) {
        if (!cancelled) {
          setError(errorMessage(err, "No se encontró la orden"));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [params.id]);

  if (loading) {
    return (
      <PanelShell title="Orden">
        <p className="text-sm text-muted">Cargando…</p>
      </PanelShell>
    );
  }

  if (error || !order) {
    return (
      <PanelShell title="Orden">
        <p className="text-sm text-red-700">{error ?? "No encontrada"}</p>
        <Link
          href="/panel"
          className="tap-target mt-4 inline-flex items-center text-sm text-brand"
        >
          ← Volver al panel
        </Link>
      </PanelShell>
    );
  }

  return (
    <PanelShell
      title={order.title}
      subtitle="Estados del trabajo y aviso al cliente"
    >
      <OrdenDetailBody
        order={order}
        setOrder={setOrder}
        draftMessage={draftMessage}
        setDraftMessage={setDraftMessage}
        draftPhone={draftPhone}
        notificationId={notificationId}
        messageSent={messageSent}
        setMessageSent={setMessageSent}
        applyDraftFrom={applyDraftFrom}
      />
    </PanelShell>
  );
}

function OrdenDetailBody({
  order,
  setOrder,
  draftMessage,
  setDraftMessage,
  draftPhone,
  notificationId,
  messageSent,
  setMessageSent,
  applyDraftFrom,
}: {
  order: ApiOrder;
  setOrder: (o: ApiOrder) => void;
  draftMessage: string;
  setDraftMessage: (v: string) => void;
  draftPhone: string;
  notificationId: string | null;
  messageSent: boolean;
  setMessageSent: (v: boolean) => void;
  applyDraftFrom: (payload: unknown, fallbackPhone?: string) => void;
}) {
  const router = useRouter();
  const leaveGuard = useLeaveGuard();
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<
    { type: "status"; status: string } | { type: "delete" } | null
  >(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [markingSent, setMarkingSent] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const hasUnsentWhatsApp = Boolean(draftMessage.trim()) && !messageSent;
  useLeaveBlock(hasUnsentWhatsApp);

  useEffect(() => {
    if (!flash) return;
    const t = setTimeout(() => setFlash(null), 3500);
    return () => clearTimeout(t);
  }, [flash]);

  const waLink =
    draftPhone && draftMessage.trim()
      ? buildWhatsAppLink(draftPhone, draftMessage.trim())
      : null;

  function requestLeavePanel(e?: React.MouseEvent) {
    if (hasUnsentWhatsApp) {
      leaveGuard?.requestNavigate("/panel", e);
      return;
    }
    router.push("/panel");
  }

  async function changeStatus(next: string) {
    if (next === order.status) return;
    setSaving(true);
    setActionError(null);
    setPendingAction({ type: "status", status: next });
    try {
      const { data } = await apiFetch<ApiOrder>(`/orders/${order.id}/status`, {
        method: "POST",
        body: JSON.stringify({ status: next }),
      });
      const normalized = normalizeOrder({
        ...order,
        ...data,
        status: (data.status as string) || next,
      });
      setOrder(normalized);
      applyDraftFrom(data, order.client?.phone);
      setMessageSent(false);
      setPendingAction(null);
      setFlash(
        `Estado actualizado a “${statusLabel(next)}”. Revisa el aviso y mándalo por WhatsApp.`,
      );
    } catch (err) {
      setActionError(errorMessage(err, "No se pudo cambiar el estado"));
    } finally {
      setSaving(false);
    }
  }

  function retryAction() {
    if (!pendingAction) return;
    if (pendingAction.type === "status") {
      void changeStatus(pendingAction.status);
      return;
    }
    void deleteOrder();
  }

  async function markSent() {
    const id = notificationId;
    const finalMessage = draftMessage.trim().slice(0, 1000);
    if (!id || !finalMessage) return;

    setMarkingSent(true);
    setSendError(null);
    try {
      await apiFetch(`/notifications/${id}/sent`, {
        method: "POST",
        body: JSON.stringify({ message: finalMessage }),
      });
      setMessageSent(true);
      setFlash("Aviso marcado como enviado.");
    } catch (err) {
      setSendError(
        errorMessage(
          err,
          "No se pudo registrar el aviso. El WhatsApp puede haberse abierto; vuelve a intentar cuando haya red.",
        ),
      );
    } finally {
      setMarkingSent(false);
    }
  }

  async function deleteOrder() {
    setDeleting(true);
    setActionError(null);
    setPendingAction({ type: "delete" });
    try {
      await apiFetch(`/orders/${order.id}`, { method: "DELETE" });
      setPendingAction(null);
      router.replace("/panel");
    } catch (err) {
      setDeleteConfirmOpen(false);
      setActionError(
        errorMessage(
          err,
          "No se pudo eliminar la orden. Si el backend aún no tiene DELETE, avísale a Claude.",
        ),
      );
    } finally {
      setDeleting(false);
    }
  }

  return (
    <>
      <div className="mb-4">
        <button
          type="button"
          onClick={(e) => requestLeavePanel(e)}
          className="tap-target inline-flex items-center text-sm text-muted hover:text-ink"
        >
          ← Volver al panel
        </button>
      </div>

      {flash && (
        <div
          role="status"
          className="animate-rise mb-4 rounded-md border border-[color:var(--ok-line)] bg-ok-soft px-4 py-3 text-sm text-[color:var(--tone-ink)]"
        >
          {flash}
        </div>
      )}

      {actionError && (
        <div
          role="alert"
          className="mb-4 flex flex-col gap-3 rounded-md border border-red-200 bg-danger-soft px-4 py-3 text-sm text-red-900 dark:text-red-200 sm:flex-row sm:items-center sm:justify-between"
        >
          <p>{actionError}</p>
          <button
            type="button"
            disabled={saving || deleting}
            onClick={() => retryAction()}
            className="tap-target shrink-0 rounded-md border border-red-300 bg-surface px-3 py-2 text-sm font-semibold disabled:opacity-60"
          >
            Reintentar
          </button>
        </div>
      )}

      <div className="grid min-w-0 gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="min-w-0 rounded-lg border border-line bg-surface p-5">
          <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 overflow-hidden">
              <p className="truncate text-sm text-muted">
                {order.vehicleOrItem}
              </p>
              <p className="mt-1 truncate font-medium text-ink">
                {order.client?.name ?? "Cliente"} ·{" "}
                {order.client?.phone ?? "—"}
              </p>
              {order.estimatedAt && (
                <p className="mt-2 text-sm text-muted">
                  Estimado: {formatDateCl(order.estimatedAt)}
                </p>
              )}
            </div>
            <StatusBadge status={order.status} />
          </div>

          {order.description && (
            <p className="mt-5 text-sm leading-relaxed text-muted">
              {order.description}
            </p>
          )}

          <label className="mt-6 block" htmlFor="order-status">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted">
              Cambiar estado
            </span>
            <select
              id="order-status"
              value={order.status}
              disabled={saving}
              onChange={(e) => changeStatus(e.target.value)}
              className={fieldClass}
              aria-busy={saving}
            >
              {ALL_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {statusLabel(s)}
                </option>
              ))}
            </select>
            {saving && (
              <p className="mt-1.5 text-sm font-medium text-muted">
                Guardando…
              </p>
            )}
          </label>
        </div>

        <div className="min-w-0 rounded-lg border border-line bg-surface p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted">
            Aviso al cliente
          </p>
          <p className="mt-1 text-sm font-medium text-ink">
            Borrador de la API — puedes editarlo antes de enviar
          </p>

          {draftMessage ? (
            <label className="mt-3 block" htmlFor="draft-message">
              <span className="sr-only">Mensaje para el cliente</span>
              <textarea
                id="draft-message"
                value={draftMessage}
                onChange={(e) => setDraftMessage(e.target.value)}
                rows={6}
                maxLength={1000}
                disabled={messageSent || markingSent}
                className={`${fieldClass} min-h-[8.5rem] resize-y leading-relaxed disabled:opacity-70`}
              />
            </label>
          ) : (
            <p className="mt-3 rounded-md border border-dashed border-line bg-chip p-3 text-sm text-muted">
              Cambia el estado de la orden para que la API genere el borrador del
              aviso.
            </p>
          )}

          {sendError && (
            <p
              role="alert"
              className="mt-3 text-sm text-red-700 dark:text-red-300"
            >
              {sendError}
            </p>
          )}

          {waLink && !messageSent ? (
            <a
              href={waLink}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => {
                void markSent();
              }}
              className="btn-brand tap-target mt-4 inline-flex w-full items-center justify-center rounded-md px-4 py-2.5 text-sm font-semibold transition active:scale-[0.99]"
            >
              {markingSent ? "Registrando aviso…" : "Avisar por WhatsApp"}
            </a>
          ) : messageSent ? (
            <p className="mt-4 text-sm font-medium text-[color:var(--tone-ink)]">
              Aviso marcado como enviado.
            </p>
          ) : (
            <p className="mt-4 text-sm text-muted">
              {draftMessage
                ? "Falta el teléfono del cliente para armar el WhatsApp."
                : "Cuando haya borrador y teléfono, podrás avisar por WhatsApp."}
            </p>
          )}
        </div>
      </div>

      <div className="mt-8 border-t border-line pt-6">
        <p className="text-sm text-muted">
          ¿Creaste esta orden por error o ya no corresponde?
        </p>
        <button
          type="button"
          onClick={() => setDeleteConfirmOpen(true)}
          className="tap-target mt-3 inline-flex items-center justify-center rounded-md border border-red-200 px-4 py-2.5 text-sm font-semibold text-red-700 hover:bg-danger-soft"
        >
          Eliminar orden
        </button>
      </div>

      {deleteConfirmOpen && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-confirm-title"
        >
          <div className="w-full max-w-md rounded-lg border border-line bg-surface p-5 shadow-xl">
            <h2
              id="delete-confirm-title"
              className="font-[family-name:var(--font-display)] text-lg font-bold text-ink"
            >
              ¿Eliminar esta orden?
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Se borrará “{order.title}”. Esta acción no se puede deshacer. El
              cliente y el vehículo se mantienen.
            </p>
            <div className="mt-5 flex flex-col gap-2 sm:flex-row-reverse">
              <button
                type="button"
                disabled={deleting}
                onClick={() => {
                  void deleteOrder();
                }}
                className="tap-target inline-flex items-center justify-center rounded-md bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800 disabled:opacity-60"
              >
                {deleting ? "Eliminando…" : "Sí, eliminar orden"}
              </button>
              <button
                type="button"
                disabled={deleting}
                onClick={() => setDeleteConfirmOpen(false)}
                className="tap-target inline-flex items-center justify-center rounded-md border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink hover:bg-chip"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

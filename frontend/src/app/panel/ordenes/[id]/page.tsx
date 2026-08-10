"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { PanelShell } from "@/components/panel-shell";
import { StatusBadge } from "@/components/ui";
import { apiFetch } from "@/lib/api";
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

const fieldClass =
  "mt-1.5 w-full rounded-md border border-line bg-white px-3 py-2.5 text-sm text-stone-900 placeholder:text-stone-500 outline-none focus:border-brand focus-visible:ring-2 focus-visible:ring-brand/30";

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
      <OrdenDetailContent />
    </AuthGuard>
  );
}

function OrdenDetailContent() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [order, setOrder] = useState<ApiOrder | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [draftMessage, setDraftMessage] = useState("");
  const [draftPhone, setDraftPhone] = useState("");
  const [notificationId, setNotificationId] = useState<string | null>(null);
  const [messageSent, setMessageSent] = useState(false);
  const [leaveConfirmOpen, setLeaveConfirmOpen] = useState(false);

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

  async function load() {
    const { data } = await apiFetch<ApiOrder>(`/orders/${params.id}`);
    const normalized = normalizeOrder(data);
    setOrder(normalized);
    applyDraftFrom(normalized, normalized.client?.phone);
    return normalized;
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        await load();
        if (!cancelled) setError(null);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "No se encontró");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  useEffect(() => {
    if (!flash) return;
    const t = setTimeout(() => setFlash(null), 3500);
    return () => clearTimeout(t);
  }, [flash]);

  const hasUnsentWhatsApp = Boolean(draftMessage.trim()) && !messageSent;

  const waLink =
    draftPhone && draftMessage.trim()
      ? buildWhatsAppLink(draftPhone, draftMessage.trim())
      : null;

  function requestLeavePanel(e?: React.MouseEvent) {
    if (hasUnsentWhatsApp) {
      e?.preventDefault();
      setLeaveConfirmOpen(true);
      return;
    }
    router.push("/panel");
  }

  async function changeStatus(next: string) {
    if (!order) return;
    setSaving(true);
    try {
      const { data } = await apiFetch<ApiOrder>(`/orders/${order.id}/status`, {
        method: "POST",
        body: JSON.stringify({ status: next }),
      });
      // Usar la notification de la respuesta; no hace falta otro GET.
      const normalized = normalizeOrder({
        ...order,
        ...data,
        status: (data.status as string) || next,
      });
      setOrder(normalized);
      applyDraftFrom(data, order.client?.phone);
      setMessageSent(false);
      setFlash(
        `Estado actualizado a “${statusLabel(next)}”. Revisa el aviso y mándalo por WhatsApp.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cambiar");
    } finally {
      setSaving(false);
    }
  }

  async function markSent() {
    const id = notificationId;
    const finalMessage = draftMessage.trim().slice(0, 1000);
    if (!id || !finalMessage) return;

    setMessageSent(true);
    setLeaveConfirmOpen(false);
    try {
      await apiFetch(`/notifications/${id}/sent`, {
        method: "POST",
        body: JSON.stringify({ message: finalMessage }),
      });
      setFlash("Aviso marcado como enviado.");
    } catch {
      // No bloquea el WhatsApp; el link ya se abrió.
    }
  }

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
        <Link href="/panel" className="mt-4 inline-flex text-sm text-brand">
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
      <div className="mb-4">
        <button
          type="button"
          onClick={(e) => requestLeavePanel(e)}
          className="text-sm text-muted hover:text-ink"
        >
          ← Volver al panel
        </button>
      </div>

      {flash && (
        <div
          role="status"
          className="animate-rise mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900"
        >
          {flash}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="rounded-lg border border-line bg-surface p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm text-muted">{order.vehicleOrItem}</p>
              <p className="mt-1 font-medium text-ink">
                {order.client?.name ?? "Cliente"} ·{" "}
                {order.client?.phone ?? "—"}
              </p>
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
            >
              {ALL_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {statusLabel(s)}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="rounded-lg border border-line bg-surface p-5">
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
                disabled={messageSent}
                className={`${fieldClass} min-h-[8.5rem] resize-y leading-relaxed disabled:opacity-70`}
              />
            </label>
          ) : (
            <p className="mt-3 rounded-md border border-dashed border-line bg-stone-50 p-3 text-sm text-muted">
              Cambia el estado de la orden para que la API genere el borrador del
              aviso.
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
              className="tap-target mt-4 inline-flex w-full items-center justify-center rounded-md bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-dark active:scale-[0.99]"
            >
              Avisar por WhatsApp
            </a>
          ) : messageSent ? (
            <p className="mt-4 text-sm font-medium text-emerald-800">
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

      {leaveConfirmOpen && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="leave-confirm-title"
        >
          <div className="w-full max-w-md rounded-lg border border-line bg-surface p-5 shadow-xl">
            <h2
              id="leave-confirm-title"
              className="font-[family-name:var(--font-display)] text-lg font-bold text-ink"
            >
              ¿Volver al panel?
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              ¿Estás seguro que quieres volver al panel? Aún no has enviado el
              mensaje por WhatsApp.
            </p>
            <div className="mt-5 flex flex-col gap-2 sm:flex-row-reverse">
              <button
                type="button"
                onClick={() => router.push("/panel")}
                className="tap-target inline-flex items-center justify-center rounded-md bg-brand px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-dark"
              >
                Sí, quiero volver al panel
              </button>
              <button
                type="button"
                onClick={() => setLeaveConfirmOpen(false)}
                className="tap-target inline-flex items-center justify-center rounded-md border border-line bg-white px-4 py-2.5 text-sm font-semibold text-stone-900 hover:bg-stone-50"
              >
                No, volver a estado
              </button>
            </div>
          </div>
        </div>
      )}
    </PanelShell>
  );
}

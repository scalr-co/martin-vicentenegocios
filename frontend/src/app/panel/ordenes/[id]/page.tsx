"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { PanelShell } from "@/components/panel-shell";
import { StatusBadge } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { getWorkshopName } from "@/lib/auth";
import {
  buildStatusMessage,
  buildWhatsAppLink,
  formatVehicleOrItem,
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
  "mt-1.5 w-full rounded-md border border-line bg-white px-3 py-2.5 text-sm outline-none focus:border-brand focus-visible:ring-2 focus-visible:ring-brand/30";

export default function OrdenDetailPage() {
  return (
    <AuthGuard>
      <OrdenDetailContent />
    </AuthGuard>
  );
}

function OrdenDetailContent() {
  const params = useParams<{ id: string }>();
  const [order, setOrder] = useState<ApiOrder | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function load() {
    const { data } = await apiFetch<ApiOrder>(`/orders/${params.id}`);
    setOrder({
      ...data,
      vehicleOrItem:
        data.vehicleOrItem ||
        formatVehicleOrItem(data.vehicle ?? null, "Sin vehículo"),
    });
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

  const notification = order?.notification || order?.latestNotification;
  const workshopName = getWorkshopName();

  const message = useMemo(() => {
    if (!order) return "";
    if (notification?.message) return notification.message;
    return buildStatusMessage(
      order.client?.name ?? "cliente",
      order,
      workshopName,
    );
  }, [order, notification, workshopName]);

  const phone = notification?.toPhone || order?.client?.phone || "";
  const waLink = phone ? buildWhatsAppLink(phone, message) : null;

  async function changeStatus(next: string) {
    if (!order) return;
    setSaving(true);
    try {
      await apiFetch(`/orders/${order.id}/status`, {
        method: "POST",
        body: JSON.stringify({ status: next }),
      });
      await load();
      setFlash(
        `Estado actualizado a “${statusLabel(next)}”. Ya puedes avisar por WhatsApp.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cambiar");
    } finally {
      setSaving(false);
    }
  }

  async function markSent() {
    if (!notification?.id) return;
    try {
      await apiFetch(`/notifications/${notification.id}/sent`, {
        method: "POST",
      });
      setFlash("Aviso marcado como enviado.");
    } catch {
      // no bloquea el WhatsApp
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
        <Link href="/panel" className="text-sm text-muted hover:text-ink">
          ← Volver al panel
        </Link>
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
            Modo actual: link (wa.me)
          </p>
          <p className="mt-3 rounded-md bg-stone-50 p-3 text-sm leading-relaxed text-ink">
            {message}
          </p>
          {waLink ? (
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
          ) : (
            <p className="mt-4 text-sm text-muted">
              Falta el teléfono del cliente para armar el WhatsApp.
            </p>
          )}
        </div>
      </div>
    </PanelShell>
  );
}

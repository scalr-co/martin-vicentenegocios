"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { PanelShell } from "@/components/panel-shell";
import { apiFetch, apiList } from "@/lib/api";
import type { ApiClient, ApiVehicle } from "@/lib/types";

const fieldClass =
  "mt-1 box-border block w-full min-w-0 max-w-full rounded-md border border-line bg-white px-3 py-2.5 text-sm text-stone-900 placeholder:text-stone-500 outline-none focus:border-brand focus-visible:ring-2 focus-visible:ring-brand/30";

export default function NuevaOrdenPage() {
  return (
    <AuthGuard>
      <NuevaOrdenContent />
    </AuthGuard>
  );
}

function NuevaOrdenContent() {
  const router = useRouter();
  const [clients, setClients] = useState<ApiClient[]>([]);
  const [loadingClients, setLoadingClients] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"existing" | "new">("existing");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await apiList<ApiClient>("/clients?limit=100");
        if (!cancelled) {
          setClients(list);
          if (list.length === 0) setMode("new");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Error al cargar clientes");
        }
      } finally {
        if (!cancelled) setLoadingClients(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaving(true);
    setError(null);

    const form = new FormData(e.currentTarget);
    const plate = String(form.get("plate") || "")
      .trim()
      .toUpperCase()
      .replace(/\s+/g, "");
    const brand = String(form.get("brand") || "").trim() || null;
    const model = String(form.get("model") || "").trim() || null;
    const title = String(form.get("title") || "").trim();
    const description = String(form.get("description") || "").trim() || null;
    const estimatedAt = String(form.get("estimatedAt") || "").trim() || null;
    const rut = String(form.get("rut") || "").trim();

    try {
      let clientId = String(form.get("clientId") || "");

      if (mode === "new") {
        const name = String(form.get("clientName") || "").trim();
        const phone = String(form.get("clientPhone") || "").replace(/\D/g, "");
        const { data: client } = await apiFetch<ApiClient>("/clients", {
          method: "POST",
          body: JSON.stringify({ name, phone, rut: rut || null }),
        });
        clientId = client.id;
      } else if (rut) {
        // Solo el rut: mandar notes acá borraría lo que el mecánico ya tenía escrito.
        await apiFetch(`/clients/${clientId}`, {
          method: "PATCH",
          body: JSON.stringify({ rut }),
        });
      }

      const { data: vehicle } = await apiFetch<ApiVehicle>("/vehicles", {
        method: "POST",
        body: JSON.stringify({ clientId, plate, brand, model }),
      });

      const { data: order } = await apiFetch<{ id: string }>("/orders", {
        method: "POST",
        body: JSON.stringify({
          clientId,
          vehicleId: vehicle.id,
          title,
          description,
          estimatedAt,
          status: "recibido",
        }),
      });

      router.replace(`/panel/ordenes/${order.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la orden");
      setSaving(false);
    }
  }

  return (
    <PanelShell
      title="Nueva orden"
      subtitle="Registra un trabajo con patente, marca y modelo"
    >
      {loadingClients ? (
        <p className="text-sm text-muted">Cargando…</p>
      ) : (
        <form
          className="max-w-xl space-y-4 rounded-lg border border-line bg-surface p-5"
          onSubmit={onSubmit}
        >
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setMode("existing")}
              disabled={clients.length === 0}
              className={`rounded-full px-3 py-1.5 text-xs font-medium ${
                mode === "existing"
                  ? "bg-steel text-white"
                  : "bg-stone-100 text-muted"
              }`}
            >
              Cliente existente
            </button>
            <button
              type="button"
              onClick={() => setMode("new")}
              className={`rounded-full px-3 py-1.5 text-xs font-medium ${
                mode === "new"
                  ? "bg-steel text-white"
                  : "bg-stone-100 text-muted"
              }`}
            >
              Cliente nuevo
            </button>
          </div>

          {mode === "existing" ? (
            <label className="block min-w-0" htmlFor="clientId">
              <span className="text-sm font-medium text-ink">Cliente</span>
              <select
                id="clientId"
                name="clientId"
                required
                className={fieldClass}
                defaultValue=""
              >
                <option value="" disabled>
                  Selecciona un cliente
                </option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block min-w-0" htmlFor="clientName">
                <span className="text-sm font-medium text-ink">Nombre</span>
                <input
                  id="clientName"
                  name="clientName"
                  required
                  className={fieldClass}
                  placeholder="Juan Pérez"
                />
              </label>
              <label className="block min-w-0" htmlFor="clientPhone">
                <span className="text-sm font-medium text-ink">WhatsApp</span>
                <input
                  id="clientPhone"
                  name="clientPhone"
                  required
                  className={fieldClass}
                  placeholder="56912345678"
                />
              </label>
            </div>
          )}

          <label className="block min-w-0" htmlFor="rut">
            <span className="text-sm font-medium text-ink">
              RUT{" "}
              <span className="font-normal text-muted">(opcional)</span>
            </span>
            <input
              id="rut"
              name="rut"
              className={fieldClass}
              placeholder="12.345.678-9"
              autoComplete="off"
              inputMode="text"
            />
          </label>

          <div className="grid gap-4 sm:grid-cols-3">
            <label className="block min-w-0" htmlFor="plate">
              <span className="text-sm font-medium text-ink">Patente</span>
              <input
                id="plate"
                name="plate"
                required
                className={`${fieldClass} uppercase`}
                placeholder="ABCD12"
              />
            </label>
            <label className="block min-w-0" htmlFor="brand">
              <span className="text-sm font-medium text-ink">Marca</span>
              <input id="brand" name="brand" className={fieldClass} placeholder="Toyota" />
            </label>
            <label className="block min-w-0" htmlFor="model">
              <span className="text-sm font-medium text-ink">Modelo</span>
              <input id="model" name="model" className={fieldClass} placeholder="Corolla" />
            </label>
          </div>

          <label className="block min-w-0" htmlFor="title">
            <span className="text-sm font-medium text-ink">Título</span>
            <input
              id="title"
              name="title"
              required
              className={fieldClass}
              placeholder="Revisión de frenos"
            />
          </label>

          <label className="block min-w-0" htmlFor="description">
            <span className="text-sm font-medium text-ink">Descripción</span>
            <textarea
              id="description"
              name="description"
              rows={4}
              className={fieldClass}
              placeholder="Qué reporta el cliente..."
            />
          </label>

          <label className="block min-w-0 overflow-hidden" htmlFor="estimatedAt">
            <span className="text-sm font-medium text-ink">
              Fecha estimada{" "}
              <span className="font-normal text-muted">(opcional)</span>
            </span>
            <input
              id="estimatedAt"
              name="estimatedAt"
              type="date"
              className={fieldClass}
            />
          </label>

          {error && (
            <p role="alert" className="text-sm text-red-700">
              {error}
            </p>
          )}

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={saving}
              className="tap-target rounded-md bg-brand px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-60"
            >
              {saving ? "Guardando…" : "Crear orden"}
            </button>
            <Link
              href="/panel"
              className="tap-target inline-flex items-center text-sm text-muted hover:text-ink"
            >
              Cancelar
            </Link>
          </div>
        </form>
      )}
    </PanelShell>
  );
}

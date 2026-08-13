"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { PanelShell } from "@/components/panel-shell";
import { ApiError, apiFetch, apiList } from "@/lib/api";
import { errorMessage, parseValidationErrors } from "@/lib/errors";
import { fieldClass } from "@/lib/form-styles";
import type { ApiClient, ApiVehicle } from "@/lib/types";

function formatRutNotes(rut: string) {
  return `RUT: ${rut}`;
}

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
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [mode, setMode] = useState<"existing" | "new">("existing");
  /** Cliente ya creado en un intento previo (evita 409 al reintentar). */
  const createdClientIdRef = useRef<string | null>(null);

  async function refreshClients() {
    const list = await apiList<ApiClient>("/clients?limit=100");
    setClients(list);
    return list;
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await refreshClients();
        if (!cancelled && list.length === 0) setMode("new");
      } catch (err) {
        if (!cancelled) {
          setError(errorMessage(err, "No se pudieron cargar los clientes"));
        }
      } finally {
        if (!cancelled) setLoadingClients(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function resolveNewClient(
    name: string,
    phone: string,
    rut: string,
  ): Promise<string> {
    if (createdClientIdRef.current) {
      return createdClientIdRef.current;
    }

    try {
      const { data: client } = await apiFetch<ApiClient>("/clients", {
        method: "POST",
        body: JSON.stringify({
          name,
          phone,
          notes: rut ? formatRutNotes(rut) : null,
        }),
      });
      createdClientIdRef.current = client.id;
      try {
        await refreshClients();
      } catch {
        // La orden puede seguir; la lista se actualiza al volver
      }
      return client.id;
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        let list: ApiClient[];
        try {
          list = await refreshClients();
        } catch {
          throw err;
        }
        const existing = list.find(
          (c) => c.phone.replace(/\D/g, "") === phone,
        );
        if (existing) {
          createdClientIdRef.current = existing.id;
          return existing.id;
        }
      }
      throw err;
    }
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setFieldErrors({});

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
        clientId = await resolveNewClient(name, phone, rut);
      } else if (rut) {
        await apiFetch(`/clients/${clientId}`, {
          method: "PATCH",
          body: JSON.stringify({ notes: formatRutNotes(rut) }),
        });
      }

      const existentes = await apiList<ApiVehicle>(
        `/vehicles?plate=${encodeURIComponent(plate)}&limit=20`,
      );
      let vehicle = existentes[0];

      if (!vehicle) {
        ({ data: vehicle } = await apiFetch<ApiVehicle>("/vehicles", {
          method: "POST",
          body: JSON.stringify({ clientId, plate, brand, model }),
        }));
      } else if (vehicle.clientId && vehicle.clientId !== clientId) {
        setError("Esa patente ya está registrada a otro cliente del taller.");
        setSaving(false);
        return;
      }

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
      const parsed = parseValidationErrors(err);
      const mapped: Record<string, string> = { ...parsed.fields };
      if (mapped.name) {
        mapped.clientName = mapped.name;
      }
      if (mapped.phone) {
        mapped.clientPhone = mapped.phone;
      }
      setFieldErrors(mapped);
      setError(
        parsed.form ||
          (Object.keys(mapped).length
            ? "Revisa los campos marcados."
            : errorMessage(err, "No se pudo crear la orden")),
      );
      setSaving(false);
    }
  }

  function fieldHint(key: string) {
    const msg = fieldErrors[key];
    if (!msg) return null;
    return (
      <p className="mt-1 text-sm text-red-700" role="alert">
        {msg}
      </p>
    );
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
              className={`tap-target rounded-full px-3 py-1.5 text-xs font-medium ${
                mode === "existing"
                  ? "bg-steel text-white"
                  : "bg-chip text-muted"
              }`}
            >
              Cliente existente
            </button>
            <button
              type="button"
              onClick={() => setMode("new")}
              className={`tap-target rounded-full px-3 py-1.5 text-xs font-medium ${
                mode === "new" ? "bg-steel text-white" : "bg-chip text-muted"
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
                  aria-invalid={Boolean(fieldErrors.clientName || fieldErrors.name)}
                />
                {fieldHint("clientName") || fieldHint("name")}
              </label>
              <label className="block min-w-0" htmlFor="clientPhone">
                <span className="text-sm font-medium text-ink">WhatsApp</span>
                <input
                  id="clientPhone"
                  name="clientPhone"
                  type="tel"
                  inputMode="numeric"
                  autoComplete="tel"
                  required
                  className={fieldClass}
                  placeholder="56912345678"
                  aria-invalid={Boolean(
                    fieldErrors.clientPhone || fieldErrors.phone,
                  )}
                />
                {fieldHint("clientPhone") || fieldHint("phone")}
              </label>
            </div>
          )}

          <label className="block min-w-0" htmlFor="rut">
            <span className="text-sm font-medium text-ink">
              RUT <span className="font-normal text-muted">(opcional)</span>
            </span>
            <input
              id="rut"
              name="rut"
              className={fieldClass}
              placeholder="12.345.678-9"
              autoComplete="off"
              inputMode="text"
            />
            {fieldHint("rut")}
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
                aria-invalid={Boolean(fieldErrors.plate)}
              />
              {fieldHint("plate")}
            </label>
            <label className="block min-w-0" htmlFor="brand">
              <span className="text-sm font-medium text-ink">Marca</span>
              <input
                id="brand"
                name="brand"
                className={fieldClass}
                placeholder="Toyota"
              />
            </label>
            <label className="block min-w-0" htmlFor="model">
              <span className="text-sm font-medium text-ink">Modelo</span>
              <input
                id="model"
                name="model"
                className={fieldClass}
                placeholder="Corolla"
              />
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
              aria-invalid={Boolean(fieldErrors.title)}
            />
            {fieldHint("title")}
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
              className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold disabled:opacity-60"
            >
              {saving ? "Guardando…" : "Crear orden"}
            </button>
            <Link
              href="/panel"
              className="tap-target inline-flex items-center px-2 text-sm text-muted hover:text-ink"
            >
              Cancelar
            </Link>
          </div>
        </form>
      )}
    </PanelShell>
  );
}

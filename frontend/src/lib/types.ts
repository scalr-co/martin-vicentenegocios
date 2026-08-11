const rawApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
if (!rawApiUrl) {
  throw new Error(
    "Falta NEXT_PUBLIC_API_URL. Defínela en .env.local o en el panel de Vercel; sin ella el frontend no sabe a qué API hablar.",
  );
}
export const API_URL = rawApiUrl;

export type OrderStatus =
  | "recibido"
  | "en_diagnostico"
  | "esperando_aprobacion"
  | "en_reparacion"
  | "esperando_repuesto"
  | "listo"
  | "entregado"
  | string;

export type ApiClient = {
  id: string;
  name: string;
  phone: string;
  notes?: string | null;
  /** Si el backend lo agrega después; hoy puede ir en notes. */
  rut?: string | null;
};

export type ApiVehicle = {
  id: string;
  clientId?: string;
  plate: string;
  brand?: string | null;
  model?: string | null;
};

export type ApiNotification = {
  id: string;
  message: string;
  toPhone: string;
  status?: string;
  createdAt?: string;
  sentAt?: string | null;
};

export type ApiOrder = {
  id: string;
  title: string;
  description?: string | null;
  status: OrderStatus;
  estimatedAt?: string | null;
  createdAt?: string;
  vehicleOrItem?: string;
  client?: Pick<ApiClient, "id" | "name" | "phone">;
  vehicle?: ApiVehicle;
  clientId?: string;
  vehicleId?: string;
  photos?: { id: string; url: string; createdAt?: string }[];
  /** Respuesta de POST /orders/{id}/status */
  notification?: ApiNotification | null;
  /** Respuesta de GET /orders/{id} */
  latestNotification?: ApiNotification | null;
};

export const STATUS_LABELS: Record<string, string> = {
  recibido: "Recibido",
  en_diagnostico: "En diagnóstico",
  esperando_aprobacion: "Esperando aprobación",
  en_reparacion: "En reparación",
  esperando_repuesto: "Esperando repuesto",
  listo: "Listo",
  entregado: "Entregado",
};

export const STATUS_COLORS: Record<string, string> = {
  recibido: "bg-stone-200 text-stone-800",
  en_diagnostico: "bg-amber-100 text-amber-900",
  esperando_aprobacion: "bg-yellow-100 text-yellow-900",
  en_reparacion: "bg-orange-100 text-orange-900",
  esperando_repuesto: "bg-sky-100 text-sky-900",
  listo: "bg-emerald-100 text-emerald-900",
  entregado: "bg-stone-100 text-stone-500",
};

export function statusLabel(status: string) {
  return STATUS_LABELS[status] ?? status;
}

export function formatVehicleOrItem(v?: ApiVehicle | null, fallback = "") {
  if (!v) return fallback;
  const name = [v.brand, v.model].filter(Boolean).join(" ");
  return name ? `${name} · Patente ${v.plate}` : `Patente ${v.plate}`;
}

export function buildWhatsAppLink(phone: string, message: string) {
  const clean = phone.replace(/\D/g, "");
  return `https://wa.me/${clean}?text=${encodeURIComponent(message)}`;
}

export type NotificationDraft = {
  id?: string;
  message: string;
  toPhone?: string;
  status?: string;
};

/** Extrae el borrador de aviso que arma el backend (status change u orden). */
export function extractNotificationDraft(
  payload: unknown,
): NotificationDraft | null {
  if (!payload || typeof payload !== "object") return null;
  const obj = payload as Record<string, unknown>;

  const candidates = [
    obj.latestNotification,
    obj.notification,
    obj.aviso,
    obj.draft,
    obj.data,
  ];

  for (const candidate of candidates) {
    if (!candidate || typeof candidate !== "object") continue;
    const n = candidate as Record<string, unknown>;
    const nested = extractNotificationDraft(n);
    if (nested) return nested;
    const message =
      (typeof n.message === "string" && n.message) ||
      (typeof n.draft === "string" && n.draft) ||
      (typeof n.draftMessage === "string" && n.draftMessage) ||
      null;
    if (message) {
      return {
        id: typeof n.id === "string" ? n.id : undefined,
        message,
        toPhone:
          (typeof n.toPhone === "string" && n.toPhone) ||
          (typeof n.phone === "string" && n.phone) ||
          undefined,
        status: typeof n.status === "string" ? n.status : undefined,
      };
    }
  }

  if (typeof obj.message === "string" && obj.message.trim()) {
    return {
      id: typeof obj.id === "string" ? obj.id : undefined,
      message: obj.message,
      toPhone:
        (typeof obj.toPhone === "string" && obj.toPhone) ||
        (typeof obj.phone === "string" && obj.phone) ||
        undefined,
      status: typeof obj.status === "string" ? obj.status : undefined,
    };
  }

  return null;
}

export function isNotificationSent(status?: string | null) {
  if (!status) return false;
  const s = status.toLowerCase();
  return (
    s === "sent" ||
    s === "enviado" ||
    s === "delivered" ||
    s === "entregado"
  );
}

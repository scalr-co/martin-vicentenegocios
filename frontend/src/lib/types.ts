export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "https://martin-vicentenegocios-production.up.railway.app";

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
};

export type ApiVehicle = {
  id: string;
  clientId?: string;
  plate: string;
  brand?: string | null;
  model?: string | null;
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
  notification?: {
    id: string;
    message: string;
    toPhone: string;
    status?: string;
  } | null;
  latestNotification?: {
    id: string;
    message: string;
    toPhone: string;
    status?: string;
  } | null;
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

export function buildStatusMessage(
  clientName: string,
  order: Pick<ApiOrder, "title" | "status" | "vehicleOrItem">,
  workshopName = "Taller",
) {
  const statusText = statusLabel(order.status);
  const vehicle = order.vehicleOrItem ?? "tu vehículo";
  if (order.status === "listo") {
    return `Hola ${clientName}, te escribe ${workshopName}. Tu trabajo "${order.title}" (${vehicle}) ya está listo para retirar. ¡Te esperamos!`;
  }
  if (order.status === "esperando_aprobacion") {
    return `Hola ${clientName}, te escribe ${workshopName}. Necesitamos tu aprobación para continuar con "${order.title}" (${vehicle}). ¿Me confirmas por este chat?`;
  }
  if (order.status === "esperando_repuesto") {
    return `Hola ${clientName}, te escribe ${workshopName}. Tu trabajo "${order.title}" (${vehicle}) está en espera de repuesto. Te avisamos cuando avancemos.`;
  }
  return `Hola ${clientName}, te escribe ${workshopName}. Actualización de tu trabajo "${order.title}" (${vehicle}): estado actual — ${statusText}.`;
}

export type OrderStatus =
  | "recibido"
  | "en_diagnostico"
  | "esperando_aprobacion"
  | "en_reparacion"
  | "esperando_repuesto"
  | "listo"
  | "entregado";

export type Client = {
  id: string;
  name: string;
  phone: string;
  notes?: string;
};

export type Vehicle = {
  id: string;
  clientId: string;
  plate: string;
  brand?: string;
  model?: string;
};

export type WorkOrder = {
  id: string;
  clientId: string;
  vehicleId: string;
  title: string;
  description: string;
  /** Armado para UI; en API real lo construye el backend */
  vehicleOrItem: string;
  status: OrderStatus;
  estimatedAt?: string;
  createdAt: string;
  photos: { id: string; url: string }[];
  client: Pick<Client, "id" | "name" | "phone">;
};

export const STATUS_LABELS: Record<OrderStatus, string> = {
  recibido: "Recibido",
  en_diagnostico: "En diagnóstico",
  esperando_aprobacion: "Esperando aprobación",
  en_reparacion: "En reparación",
  esperando_repuesto: "Esperando repuesto",
  listo: "Listo",
  entregado: "Entregado",
};

export const STATUS_COLORS: Record<OrderStatus, string> = {
  recibido: "bg-stone-200 text-stone-800",
  en_diagnostico: "bg-amber-100 text-amber-900",
  esperando_aprobacion: "bg-yellow-100 text-yellow-900",
  en_reparacion: "bg-orange-100 text-orange-900",
  esperando_repuesto: "bg-sky-100 text-sky-900",
  listo: "bg-emerald-100 text-emerald-900",
  entregado: "bg-stone-100 text-stone-500",
};

export function formatVehicleOrItem(v: Pick<Vehicle, "plate" | "brand" | "model">) {
  const name = [v.brand, v.model].filter(Boolean).join(" ");
  return name ? `${name} · Patente ${v.plate}` : `Patente ${v.plate}`;
}

export const mockClients: Client[] = [
  {
    id: "c1",
    name: "Juan Pérez",
    phone: "56912345678",
    notes: "Cliente frecuente",
  },
  {
    id: "c2",
    name: "María Soto",
    phone: "56987654321",
  },
  {
    id: "c3",
    name: "Carlos Núñez",
    phone: "56955551234",
    notes: "Prefiere WhatsApp",
  },
];

export const mockVehicles: Vehicle[] = [
  {
    id: "v1",
    clientId: "c1",
    plate: "ABCD12",
    brand: "Toyota",
    model: "Corolla",
  },
  {
    id: "v2",
    clientId: "c2",
    plate: "EFGH34",
    brand: "Chevrolet",
    model: "Spark",
  },
  {
    id: "v3",
    clientId: "c3",
    plate: "IJKL56",
    brand: "Nissan",
    model: "Navara",
  },
];

function buildOrder(
  partial: Omit<WorkOrder, "vehicleOrItem" | "client" | "photos"> & {
    photos?: WorkOrder["photos"];
  },
): WorkOrder {
  const client = mockClients.find((c) => c.id === partial.clientId)!;
  const vehicle = mockVehicles.find((v) => v.id === partial.vehicleId)!;
  return {
    ...partial,
    photos: partial.photos ?? [],
    vehicleOrItem: formatVehicleOrItem(vehicle),
    client: { id: client.id, name: client.name, phone: client.phone },
  };
}

export const mockOrders: WorkOrder[] = [
  buildOrder({
    id: "o1",
    clientId: "c1",
    vehicleId: "v1",
    title: "Revisión de frenos",
    description: "Ruido al frenar. Revisar pastillas y discos.",
    status: "en_reparacion",
    estimatedAt: "2026-08-07",
    createdAt: "2026-08-05",
  }),
  buildOrder({
    id: "o2",
    clientId: "c2",
    vehicleId: "v2",
    title: "Cambio de aceite",
    description: "Mantención 10.000 km.",
    status: "listo",
    estimatedAt: "2026-08-06",
    createdAt: "2026-08-06",
  }),
  buildOrder({
    id: "o3",
    clientId: "c3",
    vehicleId: "v3",
    title: "Diagnóstico motor",
    description: "Check engine encendido. Esperando OK del cliente.",
    status: "esperando_aprobacion",
    estimatedAt: "2026-08-08",
    createdAt: "2026-08-06",
  }),
  buildOrder({
    id: "o4",
    clientId: "c1",
    vehicleId: "v1",
    title: "Alineación y balanceo",
    description: "Vibración en carretera.",
    status: "entregado",
    createdAt: "2026-08-01",
  }),
  buildOrder({
    id: "o5",
    clientId: "c2",
    vehicleId: "v2",
    title: "Cambio de correa",
    description: "Esperando llegada de repuesto.",
    status: "esperando_repuesto",
    estimatedAt: "2026-08-12",
    createdAt: "2026-08-06",
  }),
];

export function getClient(id: string) {
  return mockClients.find((c) => c.id === id);
}

export function buildWhatsAppLink(phone: string, message: string) {
  const clean = phone.replace(/\D/g, "");
  return `https://wa.me/${clean}?text=${encodeURIComponent(message)}`;
}

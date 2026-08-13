/** Planes del producto — mismas ventajas que la landing. */

export type WorkshopPlan = "basico" | "plus";

export const PLAN_BASICO_FEATURES = [
  "Órdenes de trabajo ilimitadas",
  "Estados claros (incluye espera de aprobación y repuesto)",
  "Historial por patente",
  "Clientes y vehículos del taller",
  "Aviso al cliente por WhatsApp (link listo)",
  "1 cuenta dueño + hasta 3 mecánicos",
  "El taller crea las cuentas de sus mecánicos",
  "Soporte por WhatsApp",
  "Setup e acompañamiento inicial",
] as const;

export const PLAN_PLUS_FEATURES = [
  "Órdenes de trabajo ilimitadas",
  "Estados claros (incluye espera de aprobación y repuesto)",
  "Historial por patente",
  "Clientes y vehículos del taller",
  "Aviso al cliente por WhatsApp (link listo)",
  "1 cuenta dueño + mecánicos ilimitados",
  "El taller crea las cuentas de sus mecánicos",
  "Soporte prioritario por WhatsApp",
  "Setup e acompañamiento inicial prioritario",
  "Plantillas de aviso personalizables al taller",
  "Resumen semanal del taller",
  "Exportar clientes e historial (CSV)",
] as const;

export const MAX_MECHANICS_BASIC = 3;

export function planLabel(plan: WorkshopPlan) {
  return plan === "plus" ? "Plus" : "Básico";
}

export function planFeatures(plan: WorkshopPlan): readonly string[] {
  return plan === "plus" ? PLAN_PLUS_FEATURES : PLAN_BASICO_FEATURES;
}

export function mechanicLimit(plan: WorkshopPlan): number | null {
  return plan === "basico" ? MAX_MECHANICS_BASIC : null;
}

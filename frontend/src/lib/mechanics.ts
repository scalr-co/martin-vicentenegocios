import { apiFetch, apiList } from "@/lib/api";
import { getWorkshop } from "@/lib/auth";
import type { WorkshopPlan } from "@/lib/plans";
import { MAX_MECHANICS_BASIC } from "@/lib/plans";

/** Persona del taller según UsuarioSalida (openapi). */
export type Mechanic = {
  id: string;
  name: string;
  email: string;
  role: string;
  active: boolean;
  createdAt: string;
};

export function getWorkshopPlan(): WorkshopPlan {
  const plan = getWorkshop()?.plan;
  return plan === "plus" ? "plus" : "basico";
}

export function isMechanicRole(role?: string | null) {
  return (role || "").trim().toLowerCase() === "mechanic";
}

export function isOwnerRole(role?: string | null) {
  return (role || "").trim().toLowerCase() === "owner";
}

/** Perfiles de mecánico que el taller ve (el dueño no ocupa cupo). */
export function mechanicProfileCount(people: Mechanic[]) {
  return people.filter((m) => isMechanicRole(m.role)).length;
}

/** Aviso previo en UI. La barrera real es el 409 del servidor. */
export function canAddMechanic(
  plan: WorkshopPlan,
  people: Mechanic[],
): { ok: boolean; reason?: string } {
  const count = mechanicProfileCount(people);
  if (plan === "basico" && count >= MAX_MECHANICS_BASIC) {
    return {
      ok: false,
      reason: `El plan Básico permite ${MAX_MECHANICS_BASIC} perfiles de mecánico. Elimina uno para crear otro, o pasa a Plus.`,
    };
  }
  return { ok: true };
}

export async function listMechanics(): Promise<Mechanic[]> {
  const list = await apiList<Mechanic>("/users");
  return list
    .filter(
      (m) =>
        isOwnerRole(m.role) || (isMechanicRole(m.role) && m.active !== false),
    )
    .sort((a, b) => a.name.localeCompare(b.name, "es"));
}

export async function createMechanic(input: {
  name: string;
  email: string;
  password: string;
}): Promise<Mechanic> {
  const { data } = await apiFetch<Mechanic>("/users", {
    method: "POST",
    body: JSON.stringify({
      name: input.name.trim(),
      email: input.email.trim().toLowerCase(),
      password: input.password,
    }),
  });
  return data;
}

export async function updateMechanic(
  id: string,
  patch: { name?: string },
): Promise<Mechanic> {
  const { data } = await apiFetch<Mechanic>(`/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ name: patch.name?.trim() }),
  });
  return data;
}

/** Sale del equipo. El servidor no borra el registro (queda en el historial de órdenes). */
export async function removeMechanic(id: string): Promise<void> {
  await apiFetch(`/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ active: false }),
  });
}

export async function setMechanicPassword(
  id: string,
  password: string,
): Promise<void> {
  await apiFetch(`/users/${id}/password`, {
    method: "POST",
    body: JSON.stringify({ password }),
  });
}

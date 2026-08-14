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

/** El dueño no ocupa cupo. Solo cuentan mecánicos activos. */
export function activeMechanicCount(mechanics: Mechanic[]) {
  return mechanics.filter((m) => isMechanicRole(m.role) && m.active).length;
}

/** Aviso previo en UI. La barrera real es el 409 del servidor. */
export function canAddMechanic(
  plan: WorkshopPlan,
  mechanics: Mechanic[],
): { ok: boolean; reason?: string } {
  const activeMechanics = activeMechanicCount(mechanics);
  if (plan === "basico" && activeMechanics >= MAX_MECHANICS_BASIC) {
    return {
      ok: false,
      reason: `El plan Básico permite ${MAX_MECHANICS_BASIC} mecánicos. Quita uno del equipo para dar de alta a otra persona, o pasa a Plus para no tener tope.`,
    };
  }
  return { ok: true };
}

export async function listMechanics(): Promise<Mechanic[]> {
  const list = await apiList<Mechanic>("/users");
  return list.sort((a, b) => a.name.localeCompare(b.name, "es"));
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
  patch: { name?: string; active?: boolean },
): Promise<Mechanic> {
  const body: Record<string, unknown> = {};
  if (patch.name !== undefined) body.name = patch.name.trim();
  if (patch.active !== undefined) body.active = patch.active;
  const { data } = await apiFetch<Mechanic>(`/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  return data;
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

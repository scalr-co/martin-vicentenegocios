const TOKEN_KEY = "motorping_token";
const WORKSHOP_KEY = "motorping_workshop";
const USER_KEY = "motorping_user";

/**
 * A2-05 (auditoría): el JWT vive en localStorage y cualquier script del origen
 * puede leerlo (XSS → robo de sesión).
 *
 * Alternativa propuesta (requiere backend + acuerdo):
 * - Cookie httpOnly + Secure + SameSite=Lax/Strict emitida por la API en login
 * - Frontend deja de guardar el token; las llamadas van con credentials: "include"
 * - CSRF token o SameSite estricto según el despliegue
 * No se cambia aquí sin coordinar con el backend.
 */

export type SessionWorkshop = {
  id?: string;
  name?: string;
  phone?: string;
  /** Plan del taller (basico | plus). Viene en login /auth/me. */
  plan?: "basico" | "plus" | string;
  active?: boolean;
  status?: string;
};

export type SessionUser = {
  id?: string;
  email?: string;
  name?: string;
  /** Backend: platform_admin | owner | mechanic */
  role?: "platform_admin" | "admin" | "owner" | "mechanic" | string;
};

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setSession(
  token: string,
  workshop?: unknown,
  user?: unknown,
) {
  localStorage.setItem(TOKEN_KEY, token);
  if (workshop !== undefined) {
    if (workshop === null) localStorage.removeItem(WORKSHOP_KEY);
    else localStorage.setItem(WORKSHOP_KEY, JSON.stringify(workshop));
  }
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(WORKSHOP_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getWorkshop(): SessionWorkshop | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(WORKSHOP_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SessionWorkshop;
  } catch {
    return null;
  }
}

export function getWorkshopName(): string {
  return getWorkshop()?.name?.trim() || "Taller";
}

export function getUser(): SessionUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SessionUser;
  } catch {
    return null;
  }
}

function normalizeRole(role?: string | null) {
  return (role || "").trim().toLowerCase();
}

/** Admin de plataforma. Solo confía en el rol del login. */
export function isAdmin(): boolean {
  const role = normalizeRole(getUser()?.role);
  return (
    role === "platform_admin" ||
    role === "admin" ||
    role === "superadmin"
  );
}

/** Dueño del taller (puede gestionar /users). */
export function isOwner(): boolean {
  return normalizeRole(getUser()?.role) === "owner";
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object") return null;
  return value as Record<string, unknown>;
}

export function extractSessionFromLogin(data: Record<string, unknown>): {
  workshop: SessionWorkshop | null;
  user: SessionUser | null;
} {
  const nested = asRecord(data.data);
  const workshopRaw =
    asRecord(data.workshop) ||
    asRecord(nested?.workshop) ||
    null;

  const userRaw =
    asRecord(data.user) ||
    asRecord(nested?.user) ||
    null;

  const role =
    (typeof userRaw?.role === "string" && userRaw.role) ||
    (typeof data.role === "string" && data.role) ||
    (typeof nested?.role === "string" && nested.role) ||
    undefined;

  const workshop: SessionWorkshop | null = workshopRaw
    ? {
        id: typeof workshopRaw.id === "string" ? workshopRaw.id : undefined,
        name:
          (typeof workshopRaw.name === "string" && workshopRaw.name) ||
          (typeof workshopRaw.workshopName === "string" &&
            workshopRaw.workshopName) ||
          undefined,
        phone:
          (typeof workshopRaw.phone === "string" && workshopRaw.phone) ||
          (typeof workshopRaw.workshopPhone === "string" &&
            workshopRaw.workshopPhone) ||
          undefined,
        plan:
          typeof workshopRaw.plan === "string" ? workshopRaw.plan : undefined,
        active:
          typeof workshopRaw.active === "boolean"
            ? workshopRaw.active
            : undefined,
        status:
          typeof workshopRaw.status === "string"
            ? workshopRaw.status
            : undefined,
      }
    : null;

  const user: SessionUser | null = userRaw
    ? {
        id: typeof userRaw.id === "string" ? userRaw.id : undefined,
        email:
          (typeof userRaw.email === "string" && userRaw.email) ||
          (typeof data.email === "string" && data.email) ||
          undefined,
        name: typeof userRaw.name === "string" ? userRaw.name : undefined,
        role,
      }
    : role || typeof data.email === "string"
      ? {
          email: typeof data.email === "string" ? data.email : undefined,
          role,
        }
      : null;

  return { workshop, user };
}

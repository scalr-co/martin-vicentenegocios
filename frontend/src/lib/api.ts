import { API_URL } from "@/lib/types";
import { clearSession, getToken } from "@/lib/auth";
import { ApiError, NetworkError } from "@/lib/errors";

export { ApiError, NetworkError } from "@/lib/errors";

type ApiEnvelope<T> = {
  data?: T;
  meta?: { page?: number; limit?: number; total?: number };
  error?: { message?: string; code?: string };
};

function unwrapList<T>(payload: unknown): T[] {
  if (Array.isArray(payload)) return payload as T[];
  if (payload && typeof payload === "object") {
    const obj = payload as Record<string, unknown>;
    if (Array.isArray(obj.items)) return obj.items as T[];
    if (Array.isArray(obj.results)) return obj.results as T[];
    if (Array.isArray(obj.data)) return obj.data as T[];
  }
  return [];
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<{ data: T; meta?: ApiEnvelope<T>["meta"] }> {
  const { auth = true, headers, ...rest } = options;
  const finalHeaders = new Headers(headers);
  if (!finalHeaders.has("Content-Type") && rest.body) {
    finalHeaders.set("Content-Type", "application/json");
  }
  if (auth) {
    const token = getToken();
    if (token) finalHeaders.set("Authorization", `Bearer ${token}`);
  }

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...rest,
      headers: finalHeaders,
    });
  } catch {
    throw new NetworkError();
  }

  let json: ApiEnvelope<T> | T | null = null;
  try {
    json = (await res.json()) as ApiEnvelope<T>;
  } catch {
    json = null;
  }

  if (!res.ok) {
    const envelope = json as ApiEnvelope<T> | null;
    const detail =
      json && typeof json === "object" && "detail" in json
        ? (json as { detail: unknown }).detail
        : undefined;

    let message =
      envelope?.error?.message ||
      (typeof detail === "string" ? detail : null) ||
      `Error ${res.status}`;

    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string; loc?: unknown[] };
      const loc = Array.isArray(first.loc) ? first.loc : [];
      const field = String(loc[loc.length - 1] || "");
      if (first.msg) {
        message = field ? `${field}: ${first.msg}` : first.msg;
      }
    }

    const code = envelope?.error?.code || "ERROR";

    if (res.status === 401 && auth) {
      clearSession();
      if (
        typeof window !== "undefined" &&
        !window.location.pathname.startsWith("/login")
      ) {
        window.location.href = "/login?razon=sesion";
      }
    }

    throw new ApiError(message, code, res.status, detail);
  }

  if (json && typeof json === "object" && "data" in (json as object)) {
    const envelope = json as ApiEnvelope<T>;
    return { data: envelope.data as T, meta: envelope.meta };
  }

  return { data: json as T };
}

export async function apiList<T>(
  path: string,
  options?: RequestInit & { auth?: boolean },
): Promise<T[]> {
  const { data } = await apiFetch<unknown>(path, options);
  return unwrapList<T>(data);
}

export function extractToken(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null;
  const obj = payload as Record<string, unknown>;
  if (typeof obj.token === "string") return obj.token;
  if (typeof obj.access_token === "string") return obj.access_token;
  if (typeof obj.accessToken === "string") return obj.accessToken;
  if (obj.data && typeof obj.data === "object") {
    return extractToken(obj.data);
  }
  return null;
}

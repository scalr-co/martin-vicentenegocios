/** Error HTTP de la API. */
export class ApiError extends Error {
  code: string;
  status: number;
  detail?: unknown;

  constructor(
    message: string,
    code = "ERROR",
    status = 400,
    detail?: unknown,
  ) {
    super(message);
    this.code = code;
    this.status = status;
    this.detail = detail;
  }
}

/** Fallo de red / API inaccesible (fetch rechazado). */
export class NetworkError extends Error {
  constructor(
    message = "Sin conexión. Revisa tu red e inténtalo de nuevo.",
  ) {
    super(message);
    this.name = "NetworkError";
  }
}

export function isNetworkError(err: unknown): err is NetworkError {
  return (
    err instanceof NetworkError ||
    (err instanceof TypeError && /fetch|network|Failed to fetch/i.test(err.message))
  );
}

/** Mensaje en español para mostrar al usuario. */
export function errorMessage(
  err: unknown,
  fallback = "Algo salió mal. Inténtalo de nuevo.",
): string {
  if (err instanceof NetworkError) return err.message;
  if (isNetworkError(err)) {
    return "Sin conexión. Revisa tu red e inténtalo de nuevo.";
  }
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error && err.message && err.message !== "Failed to fetch") {
    return err.message;
  }
  return fallback;
}

const FIELD_LABELS: Record<string, string> = {
  title: "Título",
  plate: "Patente",
  brand: "Marca",
  model: "Modelo",
  description: "Descripción",
  estimatedAt: "Fecha estimada",
  estimated_at: "Fecha estimada",
  name: "Nombre",
  phone: "WhatsApp",
  clientName: "Nombre",
  clientPhone: "WhatsApp",
  rut: "RUT",
  email: "Email",
  password: "Contraseña",
  status: "Estado",
  notes: "Notas",
};

function translateValidationMsg(msg: string): string {
  const m = msg.toLowerCase();
  if (m.includes("at least 2") || m.includes("min_length")) {
    return "Debe tener al menos 2 caracteres.";
  }
  if (m.includes("required") || m.includes("field required")) {
    return "Este campo es obligatorio.";
  }
  if (
    (m.includes("patente") || m.includes("plate")) &&
    (m.includes("vacia") || m.includes("vacía") || m.includes("empty"))
  ) {
    return "La patente no puede ir vacía.";
  }
  if (m.includes("valid") && m.includes("email")) {
    return "El email no es válido.";
  }
  const cleaned = msg.replace(/^Value error,?\s*/i, "").trim();
  if (cleaned && (/[áéíóúñü]/i.test(cleaned) || /[a-zA-Z]{3,}/.test(cleaned))) {
    return cleaned.endsWith(".") ? cleaned : `${cleaned}.`;
  }
  return "Revisa este campo.";
}

type FastApiDetailItem = {
  loc?: unknown[];
  msg?: string;
  type?: string;
};

/**
 * Mapea el 422 de FastAPI (`detail: [{ loc, msg }]`) a errores por campo.
 */
export function parseValidationErrors(err: unknown): {
  fields: Record<string, string>;
  form: string | null;
} {
  const fields: Record<string, string> = {};
  let form: string | null = null;

  if (!(err instanceof ApiError) || err.status !== 422) {
    return { fields, form: errorMessage(err) };
  }

  const detail = err.detail;

  if (typeof detail === "string") {
    return { fields, form: detail };
  }

  if (Array.isArray(detail)) {
    for (const item of detail as FastApiDetailItem[]) {
      const loc = Array.isArray(item.loc) ? item.loc : [];
      const key = String(loc[loc.length - 1] || "");
      const msg = translateValidationMsg(String(item.msg || ""));
      if (key && key !== "body") {
        fields[key] = msg;
      } else {
        form = msg;
      }
    }
    if (Object.keys(fields).length === 0 && !form) {
      form = "Revisa los datos del formulario.";
    }
    return { fields, form };
  }

  return {
    fields,
    form: err.message || "Revisa los datos del formulario.",
  };
}

export function fieldLabel(key: string): string {
  return FIELD_LABELS[key] || key;
}

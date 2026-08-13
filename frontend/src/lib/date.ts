/** Formato corto chileno dd-mm-aaaa (o el string original si no parsea). */
export function formatDateCl(value?: string | null): string {
  if (!value) return "";
  const raw = value.trim();
  // date input / ISO date-only
  const dateOnly = /^(\d{4})-(\d{2})-(\d{2})/.exec(raw);
  if (dateOnly) {
    return `${dateOnly[3]}-${dateOnly[2]}-${dateOnly[1]}`;
  }
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return raw;
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const yyyy = d.getFullYear();
  return `${dd}-${mm}-${yyyy}`;
}

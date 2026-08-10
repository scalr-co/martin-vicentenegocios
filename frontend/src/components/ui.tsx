import Link from "next/link";
import { STATUS_COLORS, statusLabel } from "@/lib/types";

export function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? "bg-stone-200 text-stone-800";
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${color}`}
    >
      {statusLabel(status)}
    </span>
  );
}

export function BrandMark({
  className = "",
  light = false,
}: {
  className?: string;
  light?: boolean;
}) {
  return (
    <Link
      href="/"
      className={`font-[family-name:var(--font-display)] font-bold tracking-tight ${
        light ? "text-white" : "text-ink"
      } ${className}`}
    >
      Motor Ping
    </Link>
  );
}

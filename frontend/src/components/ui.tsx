"use client";

import Link from "next/link";
import { useSyncExternalStore } from "react";
import { getStatuses, statusLabel, subscribeStatuses } from "@/lib/statuses";
import { STATUS_COLORS } from "@/lib/types";

export function StatusBadge({ status }: { status: string }) {
  useSyncExternalStore(subscribeStatuses, getStatuses, getStatuses);
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

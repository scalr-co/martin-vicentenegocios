"use client";

import Image from "next/image";
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

const MARK_SIZES = {
  sm: 22,
  md: 28,
  lg: 36,
  xl: 48,
} as const;

export function BrandMark({
  className = "",
  light = false,
  size = "md",
  href = "/",
}: {
  className?: string;
  light?: boolean;
  size?: keyof typeof MARK_SIZES;
  href?: string;
}) {
  const px = MARK_SIZES[size];
  return (
    <Link
      href={href}
      className={`inline-flex items-center gap-2 font-[family-name:var(--font-display)] font-bold tracking-tight ${
        light ? "text-white" : "text-ink"
      } ${className}`}
    >
      <Image
        src="/brand/mark.png"
        alt=""
        width={px}
        height={px}
        className="shrink-0 rounded-md"
        priority
      />
      <span>Motor Ping</span>
    </Link>
  );
}

/** Solo el isotipo (pestaña / lugares muy chicos). */
export function BrandMarkIcon({
  className = "",
  size = 28,
}: {
  className?: string;
  size?: number;
}) {
  return (
    <Image
      src="/brand/mark.png"
      alt="Motor Ping"
      width={size}
      height={size}
      className={`rounded-md ${className}`}
    />
  );
}

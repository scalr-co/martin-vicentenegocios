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

/** Logo oficial MOTOR / PING (cuadrado). */
const LOGO_SIZES = {
  sm: 36,
  md: 44,
  lg: 56,
  xl: 72,
} as const;

export function BrandMark({
  className = "",
  size = "md",
  href = "/",
}: {
  className?: string;
  /** Se mantiene por compatibilidad; el logo ya trae su propio contraste. */
  light?: boolean;
  size?: keyof typeof LOGO_SIZES;
  href?: string;
}) {
  const px = LOGO_SIZES[size];
  return (
    <Link
      href={href}
      className={`inline-flex items-center ${className}`}
      aria-label="Motor Ping"
    >
      <Image
        src="/brand/logo.png"
        alt="Motor Ping"
        width={px}
        height={px}
        className="h-auto w-auto shrink-0 rounded-md"
        style={{ width: px, height: px }}
        priority
      />
    </Link>
  );
}

export function BrandMarkIcon({
  className = "",
  size = 32,
}: {
  className?: string;
  size?: number;
}) {
  return (
    <Image
      src="/brand/logo.png"
      alt="Motor Ping"
      width={size}
      height={size}
      className={`rounded-md ${className}`}
    />
  );
}

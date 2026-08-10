"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, isAdmin } from "@/lib/auth";

/** Solo Martín/Vicente (rol admin). Talleres normales no entran. */
export function AdminGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (!isAdmin()) {
      router.replace("/panel");
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) {
    return (
      <div className="flex min-h-dvh flex-1 items-center justify-center bg-background text-sm text-muted">
        Cargando…
      </div>
    );
  }

  return <>{children}</>;
}

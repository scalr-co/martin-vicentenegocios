"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, isOwner } from "@/lib/auth";

/** Solo el dueño del taller gestiona /users. Los mecánicos reciben 403. */
export function OwnerGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login?razon=sesion");
      return;
    }
    if (!isOwner()) {
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

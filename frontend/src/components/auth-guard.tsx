"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getToken } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      // A4-10: no dejar workshop/user del taller anterior colgados
      clearSession();
      router.replace("/login?razon=sesion");
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

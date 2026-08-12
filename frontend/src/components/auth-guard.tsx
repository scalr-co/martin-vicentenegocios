"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { clearSession, getToken, isAdmin } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      // A4-10: no dejar workshop/user del taller anterior colgados
      clearSession();
      router.replace("/login?razon=sesion");
      return;
    }
    // Admin de plataforma no usa el panel de órdenes del taller
    if (isAdmin() && !pathname.startsWith("/panel/admin")) {
      router.replace("/panel/admin");
      return;
    }
    setReady(true);
  }, [router, pathname]);

  if (!ready) {
    return (
      <div className="flex min-h-dvh flex-1 items-center justify-center bg-background text-sm text-muted">
        Cargando…
      </div>
    );
  }

  return <>{children}</>;
}

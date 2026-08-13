"use client";

import { useEffect } from "react";

const LEGACY_STORAGE_KEY = "tt-theme";

function applyTheme(theme: "light" | "dark") {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.style.colorScheme = theme;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.setAttribute("content", theme === "dark" ? "#12100e" : "#f6f1e8");
  }
}

/** Sigue el modo claro/oscuro del sistema (celular / PC). */
export function SystemThemeSync() {
  useEffect(() => {
    try {
      localStorage.removeItem(LEGACY_STORAGE_KEY);
    } catch {
      // ignore
    }

    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const sync = () => applyTheme(mq.matches ? "dark" : "light");
    sync();

    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);

  return null;
}

/** Evita flash de tema incorrecto al cargar (solo según el sistema). */
export function ThemeScript() {
  const code = `(function(){try{localStorage.removeItem('${LEGACY_STORAGE_KEY}');var d=window.matchMedia('(prefers-color-scheme: dark)').matches;if(d){document.documentElement.classList.add('dark');document.documentElement.style.colorScheme='dark';}else{document.documentElement.classList.remove('dark');document.documentElement.style.colorScheme='light';}}catch(e){}})();`;
  return <script dangerouslySetInnerHTML={{ __html: code }} />;
}

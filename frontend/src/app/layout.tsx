import type { Metadata, Viewport } from "next";
import { DM_Sans, Syne } from "next/font/google";
import { ThemeScript } from "@/components/theme-toggle";
import "./globals.css";

const body = DM_Sans({
  variable: "--font-body",
  subsets: ["latin"],
});

const display = Syne({
  variable: "--font-display",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TallerTrack — Órdenes de trabajo para talleres",
  description:
    "Registra cada trabajo, sigue el estado y avisa al cliente por WhatsApp. Hecho para talleres de Chile.",
};

export const viewport: Viewport = {
  themeColor: "#1c1917",
  viewportFit: "cover",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${body.variable} ${display.variable} h-full`}
      suppressHydrationWarning
    >
      <head>
        <ThemeScript />
      </head>
      <body className="flex min-h-dvh flex-col antialiased">{children}</body>
    </html>
  );
}

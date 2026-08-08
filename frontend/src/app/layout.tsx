import type { Metadata } from "next";
import { DM_Sans, Syne } from "next/font/google";
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

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${body.variable} ${display.variable} h-full`}>
      <body className="min-h-full flex flex-col antialiased">{children}</body>
    </html>
  );
}

# TallerTrack

Frontend del sistema de órdenes de trabajo para talleres (Chillán + Temuco).

## Stack

- Next.js (App Router) + TypeScript + Tailwind
- Datos mock por ahora (sin backend)

## Correr en local

```bash
npm install
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000)

## Rutas

- `/` — Landing
- `/login` — Ingreso (visual)
- `/panel` — Órdenes de hoy
- `/panel/clientes`
- `/panel/nueva-orden`
- `/panel/ordenes/[id]` — Detalle + WhatsApp

## Backend

Ver [BACKEND.md](./BACKEND.md) — contrato para tu amigo con Claude.

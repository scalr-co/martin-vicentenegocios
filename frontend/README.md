# Motor Ping

Frontend del sistema de órdenes de trabajo para talleres (Chillán + Temuco).

## Stack

- Next.js (App Router) + TypeScript + Tailwind
- Conectado a la API en Railway

## Correr en local

```bash
npm install
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000)

## Rutas

- `/` — Landing
- `/login` — Ingreso
- `/panel` — Órdenes de hoy
- `/panel/clientes`
- `/panel/nueva-orden`
- `/panel/ordenes/[id]` — Detalle + WhatsApp
- `/panel/admin` — Admin (solo Martín / Vicente)

## Backend

Ver [BACKEND.md](./BACKEND.md) — contrato para tu amigo con Claude.

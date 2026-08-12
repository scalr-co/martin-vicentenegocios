"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { PanelShell } from "@/components/panel-shell";
import { fieldClass } from "@/lib/form-styles";
import {
  deleteMechanic,
  getMechanic,
  updateMechanic,
  type Mechanic,
} from "@/lib/mechanics";

export default function MecanicoDetailPage() {
  return (
    <AuthGuard>
      <MecanicoDetailContent />
    </AuthGuard>
  );
}

function MecanicoDetailContent() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [mechanic, setMechanic] = useState<Mechanic | null>(null);
  const [editing, setEditing] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);

  useEffect(() => {
    setMechanic(getMechanic(params.id));
    setEditing(false);
  }, [params.id]);

  if (!mechanic) {
    return (
      <PanelShell title="Mecánico">
        <p className="text-sm text-muted">No se encontró este mecánico.</p>
        <Link
          href="/panel/mecanicos"
          className="tap-target mt-4 inline-flex text-sm text-brand"
        >
          ← Volver a mecánicos
        </Link>
      </PanelShell>
    );
  }

  function onSave(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!mechanic) return;
    const form = new FormData(e.currentTarget);
    const updated = updateMechanic(mechanic.id, {
      name: String(form.get("name") || ""),
      email: String(form.get("email") || ""),
      phone: String(form.get("phone") || ""),
      notes: String(form.get("notes") || ""),
    });
    if (updated) {
      setMechanic(updated);
      setEditing(false);
      setFlash("Cambios guardados.");
      window.setTimeout(() => setFlash(null), 2800);
    }
  }

  function onDelete() {
    if (!mechanic) return;
    deleteMechanic(mechanic.id);
    router.replace("/panel/mecanicos");
  }

  return (
    <PanelShell title={mechanic.name} subtitle="Perfil del mecánico">
      <Link
        href="/panel/mecanicos"
        className="tap-target mb-4 inline-flex items-center text-sm text-muted hover:text-ink"
      >
        ← Volver a mecánicos
      </Link>

      {flash && (
        <p
          role="status"
          className="mb-4 rounded-md border border-[color:var(--ok-line)] bg-ok-soft px-3 py-2 text-sm text-[color:var(--ok-ink)]"
        >
          {flash}
        </p>
      )}

      <form
        className="rounded-lg border border-line bg-surface p-5"
        onSubmit={onSave}
      >
        <label className="block" htmlFor="name">
          <span className="text-sm font-medium">Nombre</span>
          <input
            id="name"
            name="name"
            required
            defaultValue={mechanic.name}
            disabled={!editing}
            key={`${mechanic.id}-name-${editing}`}
            className={`${fieldClass} disabled:opacity-70`}
          />
        </label>
        <label className="mt-3 block" htmlFor="email">
          <span className="text-sm font-medium">Email</span>
          <input
            id="email"
            name="email"
            type="email"
            required
            defaultValue={mechanic.email}
            disabled={!editing}
            key={`${mechanic.id}-email-${editing}`}
            className={`${fieldClass} disabled:opacity-70`}
          />
        </label>
        <label className="mt-3 block" htmlFor="phone">
          <span className="text-sm font-medium">WhatsApp</span>
          <input
            id="phone"
            name="phone"
            type="tel"
            inputMode="numeric"
            defaultValue={mechanic.phone}
            disabled={!editing}
            key={`${mechanic.id}-phone-${editing}`}
            className={`${fieldClass} disabled:opacity-70`}
          />
        </label>
        <label className="mt-3 block" htmlFor="notes">
          <span className="text-sm font-medium">Notas</span>
          <input
            id="notes"
            name="notes"
            defaultValue={mechanic.notes ?? ""}
            disabled={!editing}
            key={`${mechanic.id}-notes-${editing}`}
            className={`${fieldClass} disabled:opacity-70`}
          />
        </label>
        <p className="mt-3 text-xs text-muted">Alta: {mechanic.createdAt}</p>

        <div className="mt-6 flex flex-wrap gap-2 border-t border-line pt-5">
          {editing ? (
            <button
              type="submit"
              className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold"
            >
              Guardar cambios
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold"
            >
              Editar
            </button>
          )}
          {editing && (
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="tap-target rounded-md border border-line px-4 py-2.5 text-sm font-semibold text-ink"
            >
              Cancelar
            </button>
          )}
          <button
            type="button"
            onClick={() => setDeleteOpen(true)}
            className="tap-target rounded-md bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800"
          >
            Eliminar
          </button>
        </div>
      </form>

      {deleteOpen && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-mec-title"
        >
          <div className="w-full max-w-md rounded-lg border border-line bg-surface p-5 shadow-xl">
            <h2
              id="delete-mec-title"
              className="font-[family-name:var(--font-display)] text-lg font-bold text-ink"
            >
              ¿Eliminar mecánico?
            </h2>
            <p className="mt-2 text-sm text-muted">
              Se quitará a “{mechanic.name}” del taller. Esta acción no se puede
              deshacer en la vista previa.
            </p>
            <div className="mt-5 flex flex-col gap-2 sm:flex-row-reverse">
              <button
                type="button"
                onClick={onDelete}
                className="tap-target rounded-md bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800"
              >
                Eliminar
              </button>
              <button
                type="button"
                onClick={() => setDeleteOpen(false)}
                className="tap-target rounded-md border border-line px-4 py-2.5 text-sm font-semibold text-ink"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </PanelShell>
  );
}

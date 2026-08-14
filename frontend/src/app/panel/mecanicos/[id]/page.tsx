"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { OwnerGuard } from "@/components/owner-guard";
import { PanelShell } from "@/components/panel-shell";
import { errorMessage } from "@/lib/errors";
import { fieldClass } from "@/lib/form-styles";
import {
  isMechanicRole,
  listMechanics,
  removeMechanic,
  setMechanicPassword,
  updateMechanic,
  type Mechanic,
} from "@/lib/mechanics";

export default function MecanicoDetailPage() {
  return (
    <AuthGuard>
      <OwnerGuard>
        <MecanicoDetailContent />
      </OwnerGuard>
    </AuthGuard>
  );
}

function MecanicoDetailContent() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [mechanic, setMechanic] = useState<Mechanic | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await listMechanics();
      setMechanic(list.find((m) => m.id === params.id) ?? null);
      setLoadError(null);
    } catch (err) {
      setLoadError(errorMessage(err, "No se pudo cargar"));
      setMechanic(null);
    } finally {
      setLoading(false);
      setEditing(false);
    }
  }, [params.id]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <PanelShell title="Mecánico">
        <p className="text-sm text-muted">Cargando…</p>
      </PanelShell>
    );
  }

  if (loadError || !mechanic) {
    return (
      <PanelShell title="Mecánico">
        <p className="text-sm text-muted">
          {loadError || "No se encontró esta persona."}
        </p>
        <Link
          href="/panel/mecanicos"
          className="tap-target mt-4 inline-flex text-sm text-brand"
        >
          ← Volver a mecánicos
        </Link>
      </PanelShell>
    );
  }

  const isMechanic = isMechanicRole(mechanic.role);

  async function onSave(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!mechanic) return;
    setError(null);
    setSaving(true);
    const form = new FormData(e.currentTarget);
    try {
      const updated = await updateMechanic(mechanic.id, {
        name: String(form.get("name") || ""),
      });
      setMechanic(updated);
      setEditing(false);
      setFlash("Cambios guardados.");
      window.setTimeout(() => setFlash(null), 2800);
    } catch (err) {
      setError(errorMessage(err, "No se pudo guardar"));
    } finally {
      setSaving(false);
    }
  }

  async function onDelete() {
    if (!mechanic || !isMechanic) return;
    setError(null);
    setSaving(true);
    try {
      await removeMechanic(mechanic.id);
      router.replace("/panel/mecanicos");
    } catch (err) {
      setError(errorMessage(err, "No se pudo eliminar"));
      setDeleteOpen(false);
      setSaving(false);
    }
  }

  async function onPassword(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!mechanic) return;
    setError(null);
    setSaving(true);
    const form = new FormData(e.currentTarget);
    try {
      await setMechanicPassword(
        mechanic.id,
        String(form.get("password") || ""),
      );
      setPasswordOpen(false);
      setFlash("Contraseña actualizada.");
      window.setTimeout(() => setFlash(null), 2800);
    } catch (err) {
      setError(errorMessage(err, "No se pudo cambiar la contraseña"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <PanelShell
      title={mechanic.name}
      subtitle={mechanic.role === "owner" ? "Dueño del taller" : "Mecánico"}
    >
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
      {error && (
        <p role="alert" className="mb-4 text-sm text-red-700">
          {error}
        </p>
      )}

      <form
        className="rounded-lg border border-line bg-surface p-5"
        onSubmit={onSave}
      >
        <span className="rounded-full bg-chip px-2.5 py-1 text-xs font-medium text-muted">
          {mechanic.role === "owner" ? "Dueño" : "Mecánico"}
        </span>

        <label className="mt-4 block" htmlFor="name">
          <span className="text-sm font-medium">Nombre</span>
          <input
            id="name"
            name="name"
            required
            minLength={2}
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
            value={mechanic.email}
            disabled
            readOnly
            className={`${fieldClass} disabled:opacity-70`}
          />
        </label>
        <p className="mt-3 text-xs text-muted">Alta: {mechanic.createdAt}</p>

        <div className="mt-6 flex flex-wrap gap-2 border-t border-line pt-5">
          {editing ? (
            <>
              <button
                type="submit"
                disabled={saving}
                className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold disabled:opacity-60"
              >
                Guardar cambios
              </button>
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="tap-target rounded-md border border-line px-4 py-2.5 text-sm font-semibold text-ink"
              >
                Cancelar
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold"
            >
              Editar
            </button>
          )}
          <button
            type="button"
            onClick={() => {
              setError(null);
              setPasswordOpen(true);
            }}
            className="tap-target rounded-md border border-line px-4 py-2.5 text-sm font-semibold text-ink"
          >
            Cambiar contraseña
          </button>
          {isMechanic && (
            <button
              type="button"
              onClick={() => setDeleteOpen(true)}
              className="tap-target rounded-md bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800"
            >
              Eliminar
            </button>
          )}
        </div>
      </form>

      {deleteOpen && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-md rounded-lg border border-line bg-surface p-5 shadow-xl">
            <h2 className="font-[family-name:var(--font-display)] text-lg font-bold text-ink">
              ¿Eliminar este perfil?
            </h2>
            <p className="mt-2 text-sm text-muted">
              “{mechanic.name}” deja de entrar al panel. En Básico queda un
              cupo libre para crear otro mecánico (máximo 3).
            </p>
            <div className="mt-5 flex flex-col gap-2 sm:flex-row-reverse">
              <button
                type="button"
                disabled={saving}
                onClick={() => void onDelete()}
                className="tap-target rounded-md bg-red-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
              >
                {saving ? "Eliminando…" : "Eliminar"}
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

      {passwordOpen && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-md rounded-lg border border-line bg-surface p-5 shadow-xl">
            <h2 className="font-[family-name:var(--font-display)] text-lg font-bold text-ink">
              Nueva contraseña
            </h2>
            <form className="mt-4 space-y-3" onSubmit={onPassword}>
              <label className="block" htmlFor="password">
                <span className="text-sm font-medium">Contraseña</span>
                <input
                  id="password"
                  name="password"
                  type="password"
                  minLength={8}
                  required
                  className={fieldClass}
                />
              </label>
              <div className="flex flex-col gap-2 sm:flex-row-reverse">
                <button
                  type="submit"
                  disabled={saving}
                  className="btn-brand tap-target rounded-md px-4 py-2.5 text-sm font-semibold disabled:opacity-60"
                >
                  Guardar
                </button>
                <button
                  type="button"
                  onClick={() => setPasswordOpen(false)}
                  className="tap-target rounded-md border border-line px-4 py-2.5 text-sm font-semibold text-ink"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </PanelShell>
  );
}

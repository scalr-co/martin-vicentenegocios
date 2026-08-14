import { apiFetch, apiList } from "@/lib/api";
import type { ApiOrder, ApiVehicle } from "@/lib/types";

export async function findVehiclesByPlate(plate: string): Promise<ApiVehicle[]> {
  const q = plate.trim();
  if (!q) return [];
  return apiList<ApiVehicle>(`/vehicles?plate=${encodeURIComponent(q)}`);
}

export async function getVehicleHistory(
  vehicleId: string,
  page = 1,
  limit = 20,
) {
  return apiFetch<ApiOrder[]>(
    `/vehicles/${vehicleId}/history?page=${page}&limit=${limit}`,
  );
}

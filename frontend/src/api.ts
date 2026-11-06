export interface Quake {
  id: string;
  time: string; // UTC ISO, ör. 2026-11-06T22:24:14Z
  lat: number;
  lon: number;
  depth: number;
  mag: number;
  mag_type: string;
  location: string;
  province: string | null;
  district: string | null;
  country: string | null;
}

export interface QuakeList {
  generated_at: string;
  source_updated_at: string | null;
  hours: number;
  count: number;
  quakes: Quake[];
}

export interface NearbyQuake extends Quake {
  distance_km: number;
}

export interface QuakeDetail {
  quake: Quake;
  nearby: NearbyQuake[];
}

export interface Health {
  status: 'ok' | 'stale';
  last_success: string | null;
  history_since: string | null;
}

export class NotFoundError extends Error {}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal, headers: { Accept: 'application/json' } });
  if (response.status === 404) throw new NotFoundError(url);
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  return (await response.json()) as T;
}

export const fetchQuakes = (hours: number, signal?: AbortSignal) =>
  getJson<QuakeList>(`/api/quakes?hours=${hours}`, signal);

export const fetchDetail = (id: string, signal?: AbortSignal) =>
  getJson<QuakeDetail>(`/api/quakes/${encodeURIComponent(id)}`, signal);

export const fetchHealth = (signal?: AbortSignal) => getJson<Health>('/api/health', signal);

/** Listeyi en yeniden eskiye sıralı tutarak ekler ya da günceller. */
export function upsertQuake(list: Quake[], quake: Quake): Quake[] {
  const index = list.findIndex((q) => q.id === quake.id);
  if (index !== -1) {
    const next = list.slice();
    next[index] = quake;
    return next;
  }
  const at = list.findIndex((q) => q.time < quake.time);
  const next = list.slice();
  next.splice(at === -1 ? next.length : at, 0, quake);
  return next;
}

import type { Quake } from './api';

export const TZ = 'Europe/Istanbul';
const TRT_OFFSET = 3 * 3600_000; // Türkiye yıl boyu UTC+3

export type WindowKey = '24s' | '7g' | '30g';

export const WINDOWS: Record<WindowKey, { hours: number; label: string; short: string }> = {
  '24s': { hours: 24, label: 'Son 24 saat', short: '24 saat' },
  '7g': { hours: 24 * 7, label: 'Son 7 gün', short: '7 gün' },
  '30g': { hours: 24 * 30, label: 'Son 30 gün', short: '30 gün' },
};

export const MAG_FILTERS = [0, 2, 3, 4] as const;

/** Büyüklük skalası: kül → sülfür → kehribar → kor → kırmızı → kızıl. Haritayla aynı değerler. */
export const MAG_SCALE: { min: number; color: string; label: string }[] = [
  { min: -Infinity, color: '#8c857c', label: '<2' },
  { min: 2, color: '#d9c36a', label: '2' },
  { min: 3, color: '#ffb020', label: '3' },
  { min: 4, color: '#ff6a1f', label: '4' },
  { min: 5, color: '#f2382b', label: '5' },
  { min: 6, color: '#ff2d6f', label: '6+' },
];

export function magColor(mag: number): string {
  let color = MAG_SCALE[0].color;
  for (const step of MAG_SCALE) if (mag >= step.min) color = step.color;
  return color;
}

const one = new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const upToOne = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 1 });
const three = new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 3, maximumFractionDigits: 3 });

export const fmtMag = (mag: number) => one.format(mag);
export const fmtKm = (km: number) => `${upToOne.format(km)} km`;
export const fmtCount = (n: number) => n.toLocaleString('tr-TR');

export function fmtCoords(lat: number, lon: number): string {
  return `${three.format(Math.abs(lat))}° ${lat >= 0 ? 'K' : 'G'}, ${three.format(Math.abs(lon))}° ${lon >= 0 ? 'D' : 'B'}`;
}

export const quakeTime = (q: Quake) => Date.parse(q.time);

export function relative(t: number, now: number): string {
  const seconds = Math.max(0, (now - t) / 1000);
  if (seconds < 60) return 'az önce';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} dk önce`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} sa önce`;
  const days = Math.floor(hours / 24);
  return `${days} gün önce`;
}

const clockFmt = new Intl.DateTimeFormat('tr-TR', { timeZone: TZ, hour: '2-digit', minute: '2-digit' });
const fullFmt = new Intl.DateTimeFormat('tr-TR', {
  timeZone: TZ, weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  hour: '2-digit', minute: '2-digit', second: '2-digit',
});
const dayFmt = new Intl.DateTimeFormat('tr-TR', { timeZone: TZ, day: 'numeric', month: 'long', weekday: 'long' });
const utcFmt = new Intl.DateTimeFormat('tr-TR', {
  timeZone: 'UTC', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
});

export const fmtClock = (t: number) => clockFmt.format(t);
export const fmtFull = (t: number) => fullFmt.format(t);
export const fmtUtc = (t: number) => `${utcFmt.format(t)} UTC`;

/** Türkiye saatine göre gün numarası (gün başlıkları ve eksen için). */
export const localDay = (t: number) => Math.floor((t + TRT_OFFSET) / 86_400_000);

export function dayHeading(t: number, now: number): string {
  const diff = localDay(now) - localDay(t);
  if (diff === 0) return 'Bugün';
  if (diff === 1) return 'Dün';
  return dayFmt.format(t);
}

/** "Akdeniz - [253.19 km] Datça (Muğla)" gibi AFAD adlarını başlık + açıklamaya ayırır. */
export function splitLocation(q: Quake): { title: string; sub: string | null } {
  const offshore = /^(.*?)\s*-\s*\[([\d.,]+)\s*km\]\s*(.+)$/.exec(q.location);
  if (offshore) {
    const km = Math.round(Number(offshore[2].replace(',', '.')));
    return { title: offshore[1], sub: `${offshore[3]} açıkları · ${km} km` };
  }
  if (q.province && !q.location.includes(q.province)) {
    return { title: q.location, sub: q.district ? `${q.district} (${q.province}) yakını` : q.province };
  }
  return { title: q.location, sub: null };
}

/** Eksen çizgileri: Türkiye saatiyle hizalı. */
export function axisTicks(start: number, end: number, key: WindowKey): { t: number; label: string; major: boolean }[] {
  const hour = 3600_000;
  const step = key === '24s' ? 3 * hour : key === '7g' ? 24 * hour : 3 * 24 * hour;
  const first = Math.ceil((start + TRT_OFFSET) / step) * step - TRT_OFFSET;
  const ticks = [];
  for (let t = first; t <= end; t += step) {
    const d = new Date(t + TRT_OFFSET); // UTC alanları artık Türkiye saatini gösterir
    let label: string;
    if (key === '24s') label = `${String(d.getUTCHours()).padStart(2, '0')}:00`;
    else if (key === '7g') label = `${['Paz', 'Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt'][d.getUTCDay()]} ${d.getUTCDate()}`;
    else label = `${d.getUTCDate()} ${['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'][d.getUTCMonth()]}`;
    ticks.push({ t, label, major: key === '24s' ? d.getUTCHours() === 0 : true });
  }
  return ticks;
}

export const afadUrl = (id: string) => `https://deprem.afad.gov.tr/event-detail/${encodeURIComponent(id)}`;

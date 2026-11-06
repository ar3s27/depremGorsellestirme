import { useState } from 'react';
import type { NearbyQuake, Quake } from '../api';
import { afadUrl, fmtCoords, fmtFull, fmtKm, fmtMag, fmtUtc, magColor, quakeTime, relative, splitLocation } from '../format';

interface Props {
  quake: Quake;
  nearby: NearbyQuake[] | null;
  now: number;
  onSelect: (id: string) => void;
  onClose: () => void;
}

export default function Detail({ quake, nearby, now, onSelect, onClose }: Props) {
  const [copied, setCopied] = useState(false);
  const t = quakeTime(quake);
  const { title, sub } = splitLocation(quake);
  const color = magColor(quake.mag);

  const copyLink = async () => {
    const url = `${location.origin}/?q=${encodeURIComponent(quake.id)}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      window.prompt('Bağlantı', url);
    }
  };

  const before = nearby?.filter((q) => q.time < quake.time).length ?? 0;
  const after = (nearby?.length ?? 0) - before;

  return (
    <article className="detail" aria-label="Deprem ayrıntısı" style={{ '--c': color } as React.CSSProperties}>
      <button className="detail__close" onClick={onClose} aria-label="Kapat">
        <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 3l10 10M13 3L3 13" /></svg>
      </button>
      <div className="detail__top">
        <div className="detail__mag">
          <span className="detail__mag-value">{fmtMag(quake.mag)}</span>
          <span className="detail__mag-type">{quake.mag_type}</span>
        </div>
        <div className="detail__where">
          <h2>{title}</h2>
          {sub && <p>{sub}</p>}
          <p className="detail__ago">{relative(t, now)}</p>
        </div>
      </div>

      <dl className="detail__facts">
        <div><dt>Zaman (TSİ)</dt><dd>{fmtFull(t)}</dd></div>
        <div><dt>UTC</dt><dd>{fmtUtc(t)}</dd></div>
        <div><dt>Derinlik</dt><dd>{fmtKm(quake.depth)}</dd></div>
        <div><dt>Konum</dt><dd>{fmtCoords(quake.lat, quake.lon)}</dd></div>
      </dl>

      <div className="detail__nearby">
        <h3>50 km çevresi, ±7 gün</h3>
        {nearby === null ? (
          <p className="muted">Yükleniyor…</p>
        ) : nearby.length === 0 ? (
          <p className="muted">Bu bölgede kayıtlı başka deprem yok.</p>
        ) : (
          <>
            <p className="muted">
              Öncesinde {before}, sonrasında {after} deprem.
            </p>
            <ul>
              {nearby.slice(0, 6).map((q) => (
                <li key={q.id}>
                  <button onClick={() => onSelect(q.id)}>
                    <b style={{ color: magColor(q.mag) }}>{fmtMag(q.mag)}</b>
                    <span>{relative(quakeTime(q), now)}</span>
                    <span className="muted">{fmtKm(q.distance_km)} uzakta</span>
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="detail__actions">
        <button className="btn" onClick={copyLink}>{copied ? 'Kopyalandı' : 'Bağlantıyı kopyala'}</button>
        <a className="btn btn--ghost" href={afadUrl(quake.id)} target="_blank" rel="noopener noreferrer">
          AFAD kaydı ↗
        </a>
      </div>
    </article>
  );
}

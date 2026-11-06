import { Fragment, useState } from 'react';
import type { Quake } from '../api';
import {
  MAG_FILTERS, MAG_SCALE, WINDOWS, type WindowKey,
  dayHeading, fmtClock, fmtCount, fmtKm, fmtMag, localDay, magColor, quakeTime, relative, splitLocation,
} from '../format';
import type { LiveState } from '../hooks';

export function Wordmark() {
  return (
    <span className="wordmark">
      <svg viewBox="0 0 32 20" aria-hidden="true">
        <path d="M1 11h6l2-6 3 12 3-15 3 13 2-4h11" />
      </svg>
      sismik
    </span>
  );
}

const LIVE_TEXT: Record<LiveState, string> = { live: 'Canlı', connecting: 'Bağlanıyor', retrying: 'Yeniden bağlanıyor' };

export function Header({ live, sourceAt, now }: { live: LiveState; sourceAt: number | null; now: number }) {
  return (
    <header className="head">
      <div>
        <Wordmark />
        <p className="head__sub">Türkiye ve çevresi · AFAD verisi</p>
      </div>
      <div className={`live live--${live}`} role="status">
        <span className="live__dot" aria-hidden="true" />
        <span className="live__text">{LIVE_TEXT[live]}</span>
        {sourceAt && <span className="live__age">veri {relative(sourceAt, now)}</span>}
      </div>
    </header>
  );
}

export function Stats({ quakes, windowKey, now, onSelect }: { quakes: Quake[]; windowKey: WindowKey; now: number; onSelect: (id: string) => void }) {
  const biggest = quakes.reduce<Quake | null>((best, q) => (!best || q.mag > best.mag ? q : best), null);
  const last = quakes[0] ?? null;
  const strong = quakes.filter((q) => q.mag >= 3).length;
  return (
    <section className="stats" aria-label="Özet">
      <div className="stat">
        <span className="stat__label">{WINDOWS[windowKey].label}</span>
        <span className="stat__value">{fmtCount(quakes.length)}</span>
        <span className="stat__sub">deprem · 3+: {fmtCount(strong)}</span>
      </div>
      <button className="stat stat--link" disabled={!biggest} onClick={() => biggest && onSelect(biggest.id)}>
        <span className="stat__label">En büyük</span>
        <span className="stat__value" style={{ color: biggest ? magColor(biggest.mag) : undefined }}>
          {biggest ? fmtMag(biggest.mag) : '—'}
        </span>
        <span className="stat__sub">{biggest ? splitLocation(biggest).title : 'kayıt yok'}</span>
      </button>
      <button className="stat stat--link" disabled={!last} onClick={() => last && onSelect(last.id)}>
        <span className="stat__label">Son deprem</span>
        <span className="stat__value stat__value--time">{last ? relative(quakeTime(last), now) : '—'}</span>
        <span className="stat__sub">{last ? `${fmtMag(last.mag)} · ${splitLocation(last).title}` : 'kayıt yok'}</span>
      </button>
    </section>
  );
}

interface FiltersProps {
  windowKey: WindowKey;
  minMag: number;
  onWindow: (key: WindowKey) => void;
  onMinMag: (mag: number) => void;
}

export function Filters({ windowKey, minMag, onWindow, onMinMag }: FiltersProps) {
  return (
    <section className="filters" aria-label="Filtreler">
      <div className="seg" role="group" aria-label="Zaman aralığı">
        {(Object.keys(WINDOWS) as WindowKey[]).map((key) => (
          <button key={key} aria-pressed={key === windowKey} onClick={() => onWindow(key)}>
            {WINDOWS[key].short}
          </button>
        ))}
      </div>
      <div className="seg" role="group" aria-label="En küçük büyüklük">
        {MAG_FILTERS.map((mag) => (
          <button key={mag} aria-pressed={mag === minMag} onClick={() => onMinMag(mag)}>
            {mag === 0 ? 'Tümü' : `${mag}+`}
          </button>
        ))}
      </div>
    </section>
  );
}

export function Legend() {
  return (
    <div className="legend" aria-label="Büyüklük renkleri">
      <span className="legend__title">Büyüklük</span>
      {MAG_SCALE.map((step) => (
        <span key={step.label} className="legend__item">
          <i style={{ background: step.color }} />
          {step.label}
        </span>
      ))}
    </div>
  );
}

const PAGE = 120;

interface ListProps {
  quakes: Quake[];
  now: number;
  minMag: number;
  loading: boolean;
  failed: boolean;
  selectedId: string | null;
  freshIds: Set<string>;
  onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
}

export function QuakeList({ quakes, now, minMag, loading, failed, selectedId, freshIds, onSelect, onHover }: ListProps) {
  const [shown, setShown] = useState(PAGE);
  if (failed && quakes.length === 0) return <p className="empty">Veriye ulaşılamadı. Birkaç saniye içinde yeniden deneniyor…</p>;
  if (loading && quakes.length === 0) return <p className="empty">Depremler yükleniyor…</p>;
  if (quakes.length === 0) return <p className="empty">Bu aralıkta {minMag > 0 ? `${minMag} ve üzeri ` : ''}deprem yok.</p>;

  const visible = quakes.slice(0, shown);
  let lastDay = -1;
  return (
    <section className="list" aria-label="Deprem listesi" onMouseLeave={() => onHover(null)}>
      {visible.map((quake) => {
        const t = quakeTime(quake);
        const day = localDay(t);
        const heading = day !== lastDay ? dayHeading(t, now) : null;
        lastDay = day;
        const { title, sub } = splitLocation(quake);
        return (
          <Fragment key={quake.id}>
            {heading && <h3 className="list__day">{heading}</h3>}
            <button
              className="row"
              data-selected={quake.id === selectedId || undefined}
              data-fresh={freshIds.has(quake.id) || undefined}
              onClick={() => onSelect(quake.id)}
              onMouseEnter={() => onHover(quake.id)}
              onFocus={() => onHover(quake.id)}
            >
              <span
                className={quake.mag >= 4 ? 'row__mag row__mag--strong' : 'row__mag'}
                style={{ '--c': magColor(quake.mag) } as React.CSSProperties}
              >
                {fmtMag(quake.mag)}
              </span>
              <span className="row__main">
                <span className="row__title">{title}</span>
                <span className="row__sub">{[sub, `${fmtKm(quake.depth)} derinlik`].filter(Boolean).join(' · ')}</span>
              </span>
              <span className="row__time">
                <span>{relative(t, now)}</span>
                <span className="row__clock">{fmtClock(t)}</span>
              </span>
            </button>
          </Fragment>
        );
      })}
      {quakes.length > shown && (
        <button className="more" onClick={() => setShown((n) => n + PAGE)}>
          Daha fazla göster ({fmtCount(quakes.length - shown)} kaldı)
        </button>
      )}
    </section>
  );
}

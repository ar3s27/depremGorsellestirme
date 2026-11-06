import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { NotFoundError, type NearbyQuake, type Quake, fetchDetail, fetchHealth, fetchQuakes, upsertQuake } from './api';
import Detail from './components/Detail';
import MapView from './components/MapView';
import { Filters, Header, Legend, QuakeList, Stats } from './components/Panel';
import Seismogram from './components/Seismogram';
import Toasts, { type Toast } from './components/Toasts';
import { MAG_FILTERS, WINDOWS, type WindowKey, quakeTime } from './format';
import { useLiveFeed, useNow } from './hooks';

const FRESH_FOR = 90_000; // listede "yeni geldi" vurgusu
const TOAST_MIN_MAG = 3;

function readUrl(): { w: WindowKey; m: number; q: string | null } {
  const params = new URLSearchParams(location.search);
  const w = params.get('w') as WindowKey | null;
  const m = Number(params.get('m'));
  return {
    w: w && w in WINDOWS ? w : '24s',
    m: (MAG_FILTERS as readonly number[]).includes(m) ? m : 0,
    q: params.get('q'),
  };
}

export default function App() {
  const initial = useMemo(readUrl, []);
  const [windowKey, setWindowKey] = useState<WindowKey>(initial.w);
  const [minMag, setMinMag] = useState(initial.m);
  const [selectedId, setSelectedId] = useState<string | null>(initial.q);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [quakes, setQuakes] = useState<Quake[]>([]);
  const [loadState, setLoadState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [reloadKey, setReloadKey] = useState(0);
  const [sourceAt, setSourceAt] = useState<number | null>(null);
  const [fresh, setFresh] = useState<Map<string, number>>(new Map());
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [detail, setDetail] = useState<{ quake: Quake; nearby: NearbyQuake[] } | null>(null);
  const toastKey = useRef(0);
  const now = useNow(15_000);

  const hours = WINDOWS[windowKey].hours;
  const windowMs = hours * 3600_000;

  // Seçili aralığın depremlerini yükle (hata olursa 10 sn sonra yeniden dene).
  useEffect(() => {
    const abort = new AbortController();
    let retry = 0;
    setLoadState('loading');
    fetchQuakes(hours, abort.signal)
      .then((data) => {
        setQuakes(data.quakes);
        if (data.source_updated_at) setSourceAt(Date.parse(data.source_updated_at));
        setLoadState('ready');
      })
      .catch(() => {
        if (abort.signal.aborted) return;
        setLoadState('error');
        retry = window.setTimeout(() => setReloadKey((k) => k + 1), 10_000);
      });
    return () => {
      abort.abort();
      window.clearTimeout(retry);
    };
  }, [hours, reloadKey]);

  // Kaynağın tazeliği (AFAD'dan son başarılı çekim) dakikada bir.
  useEffect(() => {
    const id = window.setInterval(() => {
      fetchHealth()
        .then((h) => h.last_success && setSourceAt(Date.parse(h.last_success)))
        .catch(() => undefined);
    }, 60_000);
    return () => window.clearInterval(id);
  }, []);

  const pushToast = useCallback((quake: Quake) => {
    const key = ++toastKey.current;
    setToasts((list) => [...list.slice(-2), { key, quake }]);
    window.setTimeout(() => setToasts((list) => list.filter((t) => t.key !== key)), 7000);
  }, []);

  const live = useLiveFeed(
    (kind, quake) => {
      setQuakes((list) => upsertQuake(list, quake));
      setSourceAt(Date.now());
      if (kind === 'new') {
        setFresh((map) => new Map(map).set(quake.id, Date.now()));
        if (quake.mag >= TOAST_MIN_MAG) pushToast(quake);
      }
      setDetail((d) => (d && d.quake.id === quake.id ? { ...d, quake } : d));
    },
    () => setReloadKey((k) => k + 1),
  );

  // Eski "yeni" işaretlerini temizle.
  useEffect(() => {
    setFresh((map) => {
      const next = new Map([...map].filter(([, at]) => now - at < FRESH_FOR));
      return next.size === map.size ? map : next;
    });
  }, [now]);

  const inWindow = useMemo(() => quakes.filter((q) => quakeTime(q) >= now - windowMs), [quakes, now, windowMs]);
  const visible = useMemo(() => inWindow.filter((q) => q.mag >= minMag), [inWindow, minMag]);
  const freshIds = useMemo(() => new Set(fresh.keys()), [fresh]);

  // Seçilen depremin ayrıntısı (aralık dışındaysa da buradan gelir).
  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    const abort = new AbortController();
    setDetail((d) => (d?.quake.id === selectedId ? d : null));
    fetchDetail(selectedId, abort.signal)
      .then(setDetail)
      .catch((error) => {
        if (error instanceof NotFoundError) setSelectedId(null);
      });
    return () => abort.abort();
  }, [selectedId]);

  const selected = (selectedId && (quakes.find((q) => q.id === selectedId) ?? (detail?.quake.id === selectedId ? detail.quake : null))) || null;

  // Adres çubuğu: paylaşılabilir görünüm.
  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedId) params.set('q', selectedId);
    if (windowKey !== '24s') params.set('w', windowKey);
    if (minMag) params.set('m', String(minMag));
    const query = params.toString();
    history.replaceState(null, '', query ? `?${query}` : location.pathname);
  }, [selectedId, windowKey, minMag]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setSelectedId(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const select = useCallback((id: string | null) => setSelectedId(id), []);

  return (
    <div className="app">
      <main className="stage">
        <MapView
          quakes={visible}
          now={now}
          windowMs={windowMs}
          selected={selected}
          hoverId={hoverId}
          onSelect={select}
          onHover={setHoverId}
        />
        <Legend />
        <Toasts toasts={toasts} onOpen={select} onDismiss={(key) => setToasts((list) => list.filter((t) => t.key !== key))} />
        <Seismogram
          quakes={visible}
          now={now}
          windowMs={windowMs}
          windowKey={windowKey}
          hoverId={hoverId}
          selectedId={selectedId}
          onHover={setHoverId}
          onSelect={select}
        />
      </main>

      <aside className="panel">
        <Header live={live} sourceAt={sourceAt} now={now} />
        <Stats quakes={visible} windowKey={windowKey} now={now} onSelect={select} />
        <Filters windowKey={windowKey} minMag={minMag} onWindow={setWindowKey} onMinMag={setMinMag} />
        {selected && (
          <Detail
            quake={selected}
            nearby={detail?.quake.id === selected.id ? detail.nearby : null}
            now={now}
            onSelect={select}
            onClose={() => setSelectedId(null)}
          />
        )}
        <QuakeList
          key={`${windowKey}-${minMag}`}
          quakes={visible}
          now={now}
          minMag={minMag}
          loading={loadState === 'loading'}
          failed={loadState === 'error'}
          selectedId={selectedId}
          freshIds={freshIds}
          onSelect={select}
          onHover={setHoverId}
        />
        <footer className="foot">
          <span>Kaynak: <a href="https://deprem.afad.gov.tr" target="_blank" rel="noopener noreferrer">AFAD</a> · saatler TSİ</span>
          <span>
            <a href="/api/docs">API</a> · <a href="https://github.com/ar3s27/depremGorsellestirme" target="_blank" rel="noopener noreferrer">Kaynak kod</a>
          </span>
        </footer>
      </aside>
    </div>
  );
}

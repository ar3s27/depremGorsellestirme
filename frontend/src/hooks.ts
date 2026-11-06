import { useEffect, useRef, useState } from 'react';
import type { Quake } from './api';

/** Belirli aralıklarla güncellenen "şimdi" (göreli zamanlar ve pencere kayması için). */
export function useNow(intervalMs: number): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), intervalMs);
    return () => window.clearInterval(id);
  }, [intervalMs]);
  return now;
}

export type LiveState = 'connecting' | 'live' | 'retrying';

/** /api/stream canlı akışı. Bağlantı koptuktan sonra yeniden açılınca onReconnect çağrılır
 *  (aradaki depremler kaçmasın diye liste yeniden yüklenir). */
export function useLiveFeed(onQuake: (kind: 'new' | 'update', quake: Quake) => void, onReconnect: () => void): LiveState {
  const [state, setState] = useState<LiveState>('connecting');
  const handlers = useRef({ onQuake, onReconnect });
  handlers.current = { onQuake, onReconnect };

  useEffect(() => {
    const source = new EventSource('/api/stream');
    let dropped = false;
    const handle = (kind: 'new' | 'update') => (event: MessageEvent<string>) => {
      try {
        handlers.current.onQuake(kind, JSON.parse(event.data) as Quake);
      } catch {
        /* bozuk olayı yok say */
      }
    };
    source.addEventListener('new', handle('new'));
    source.addEventListener('update', handle('update'));
    source.onopen = () => {
      setState('live');
      if (dropped) handlers.current.onReconnect();
      dropped = false;
    };
    source.onerror = () => {
      dropped = true;
      setState('retrying');
    };
    return () => source.close();
  }, []);

  return state;
}

export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(query.matches);
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);
  return reduced;
}

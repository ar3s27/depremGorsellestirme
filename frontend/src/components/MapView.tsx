import maplibregl, { type ExpressionSpecification, type GeoJSONSource, type Map as MLMap } from 'maplibre-gl';
import type { Feature, FeatureCollection } from 'geojson';
import { useEffect, useRef, useState } from 'react';
import type { Quake } from '../api';
import { MAG_SCALE, fmtKm, fmtMag, magColor, quakeTime, relative, splitLocation } from '../format';
import { usePrefersReducedMotion } from '../hooks';
import { FALLBACK_STYLE, loadBaseStyle } from '../mapStyle';

const TR_BOUNDS: [[number, number], [number, number]] = [[24.6, 34.8], [45.2, 42.6]];
const FRESH_MS = 60 * 60_000; // son bir saatin depremleri nabız gibi atar
const EMPTY: FeatureCollection = { type: 'FeatureCollection', features: [] };

const COLOR = ['step', ['get', 'mag'], ...MAG_SCALE.flatMap((s, i) => (i === 0 ? [s.color] : [s.min, s.color]))] as unknown as ExpressionSpecification;
// Yarıçap büyüklükle üstel büyür (büyüklük logaritmik bir ölçek); yakınlaştıkça iri görünür.
const BASE = ['interpolate', ['exponential', 1.7], ['get', 'mag'], 0, 1.8, 2, 3.2, 3, 5, 4, 8.5, 5, 14, 6, 22, 7, 34];
const radius = (scale = 1, add = 0) =>
  ['interpolate', ['linear'], ['zoom'], 4, ['+', ['*', BASE, scale], add], 10, ['+', ['*', BASE, scale * 2.4], add]] as unknown as ExpressionSpecification;

interface Props {
  quakes: Quake[];
  now: number;
  windowMs: number;
  selected: Quake | null;
  hoverId: string | null;
  onSelect: (id: string | null) => void;
  onHover: (id: string | null) => void;
}

function popupContent(q: Quake, now: number): HTMLElement {
  const root = document.createElement('div');
  root.className = 'pop';
  const mag = document.createElement('b');
  mag.className = 'pop__mag';
  mag.style.color = magColor(q.mag);
  mag.textContent = fmtMag(q.mag);
  const text = document.createElement('div');
  const title = document.createElement('span');
  title.className = 'pop__title';
  title.textContent = splitLocation(q).title;
  const meta = document.createElement('span');
  meta.className = 'pop__meta';
  meta.textContent = `${relative(quakeTime(q), now)} · ${fmtKm(q.depth)} derinlik`;
  text.append(title, meta);
  root.append(mag, text);
  return root;
}

export default function MapView({ quakes, now, windowMs, selected, hoverId, onSelect, onHover }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MLMap | null>(null);
  const [ready, setReady] = useState(false);
  const [baseFailed, setBaseFailed] = useState(false);
  const reducedMotion = usePrefersReducedMotion();
  const latest = useRef({ quakes, now, onSelect, onHover });
  latest.current = { quakes, now, onSelect, onHover };

  // Haritayı bir kez kur.
  useEffect(() => {
    const abort = new AbortController();
    let map: MLMap | null = null;
    (async () => {
      let style = FALLBACK_STYLE;
      try {
        style = await loadBaseStyle(abort.signal);
      } catch {
        if (abort.signal.aborted) return;
        setBaseFailed(true);
      }
      if (abort.signal.aborted || !container.current) return;
      map = new maplibregl.Map({
        container: container.current,
        style,
        bounds: TR_BOUNDS,
        fitBoundsOptions: { padding: 16 },
        attributionControl: { compact: true },
        dragRotate: false,
        pitchWithRotate: false,
        touchPitch: false,
        minZoom: 3,
        maxZoom: 12,
      });
      map.touchZoomRotate.disableRotation();
      map.keyboard.disableRotation();
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
      mapRef.current = map;

      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10, className: 'pop-wrap' });
      map.on('load', () => {
        if (!map) return;
        map.addSource('quakes', { type: 'geojson', data: EMPTY });
        map.addSource('fresh', { type: 'geojson', data: EMPTY });
        map.addLayer({
          id: 'quake-glow', type: 'circle', source: 'quakes', filter: ['>=', ['get', 'mag'], 4],
          paint: { 'circle-radius': radius(2.6), 'circle-color': COLOR, 'circle-blur': 1, 'circle-opacity': 0.3 },
        });
        map.addLayer({
          id: 'quake', type: 'circle', source: 'quakes',
          layout: { 'circle-sort-key': ['-', 0, ['get', 'mag']] }, // küçükler büyüklerin üstünde kalsın
          paint: {
            'circle-radius': radius(),
            'circle-color': COLOR,
            'circle-opacity': ['get', 'fade'],
            'circle-stroke-width': 1,
            'circle-stroke-color': '#0e0c0b',
            'circle-stroke-opacity': ['get', 'fade'],
          },
        });
        map.addLayer({
          id: 'fresh-pulse', type: 'circle', source: 'fresh',
          paint: { 'circle-radius': 8, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-width': 1.5, 'circle-stroke-color': COLOR, 'circle-stroke-opacity': 0.8 },
        });
        map.addLayer({
          id: 'quake-hover', type: 'circle', source: 'quakes', filter: ['==', ['get', 'id'], ''],
          paint: { 'circle-radius': radius(1, 4), 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-width': 1.5, 'circle-stroke-color': '#efe7dc', 'circle-stroke-opacity': 0.55 },
        });
        map.addLayer({
          id: 'quake-selected', type: 'circle', source: 'quakes', filter: ['==', ['get', 'id'], ''],
          paint: { 'circle-radius': radius(1, 6), 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-width': 2, 'circle-stroke-color': '#efe7dc' },
        });

        map.on('mousemove', 'quake', (event) => {
          const id = event.features?.[0]?.properties?.id as string | undefined;
          const quake = id ? latest.current.quakes.find((q) => q.id === id) : undefined;
          if (!map || !quake) return;
          map.getCanvas().style.cursor = 'pointer';
          latest.current.onHover(quake.id);
          popup.setLngLat([quake.lon, quake.lat]).setDOMContent(popupContent(quake, latest.current.now)).addTo(map);
        });
        map.on('mouseleave', 'quake', () => {
          if (map) map.getCanvas().style.cursor = '';
          latest.current.onHover(null);
          popup.remove();
        });
        map.on('click', 'quake', (event) => {
          const id = event.features?.[0]?.properties?.id as string | undefined;
          if (id) latest.current.onSelect(id);
        });
        setReady(true);
      });
    })();
    return () => {
      abort.abort();
      map?.remove();
      mapRef.current = null;
      setReady(false);
    };
  }, []);

  // Veri: her deprem bir nokta; pencerede eskidikçe soluklaşır.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const features = quakes.map((q): Feature => {
      const age = Math.min(1, Math.max(0, (now - quakeTime(q)) / windowMs));
      return {
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [q.lon, q.lat] },
        properties: { id: q.id, mag: q.mag, fade: 1 - 0.55 * age },
      };
    });
    (map.getSource('quakes') as GeoJSONSource).setData({ type: 'FeatureCollection', features });
    const fresh = features.filter((_, i) => now - quakeTime(quakes[i]) < FRESH_MS);
    (map.getSource('fresh') as GeoJSONSource).setData({ type: 'FeatureCollection', features: fresh });
  }, [quakes, now, windowMs, ready]);

  // Taze depremlerin nabzı.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    if (reducedMotion) {
      map.setPaintProperty('fresh-pulse', 'circle-radius', 14);
      return;
    }
    let frame = 0;
    const tick = (t: number) => {
      const phase = (t % 2200) / 2200;
      map.setPaintProperty('fresh-pulse', 'circle-radius', 6 + phase * 30);
      map.setPaintProperty('fresh-pulse', 'circle-stroke-opacity', 0.85 * (1 - phase));
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [ready, reducedMotion]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    map.setFilter('quake-hover', ['==', ['get', 'id'], hoverId ?? '']);
  }, [hoverId, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    map.setFilter('quake-selected', ['==', ['get', 'id'], selected?.id ?? '']);
    if (!selected) return;
    const target = { center: [selected.lon, selected.lat] as [number, number], zoom: Math.max(map.getZoom(), 6.4) };
    if (reducedMotion) map.jumpTo(target);
    else map.flyTo({ ...target, speed: 1.4, curve: 1.3 });
    // Yalnızca seçim değişince uç; aynı depremin verisi güncellenince değil.
  }, [selected?.id, ready]);

  return (
    <div className="map" aria-label="Deprem haritası">
      <div ref={container} className="map__canvas" />
      {baseFailed && <p className="map__note">Harita altlığı yüklenemedi; depremler düz zemin üzerinde gösteriliyor.</p>}
    </div>
  );
}

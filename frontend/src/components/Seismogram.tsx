import { useEffect, useMemo, useRef, useState } from 'react';
import type { Quake } from '../api';
import { WINDOWS, type WindowKey, axisTicks, fmtMag, magColor, quakeTime, relative, splitLocation } from '../format';

/**
 * Sismogram şeridi: seçili zaman aralığındaki her deprem, zamanına denk gelen yerde
 * büyüklüğüyle orantılı sönümlü bir dalga olarak çizilir. Taban gürültüsü mutlak zamana
 * bağlıdır; böylece pencere kaydıkça çizgi zıplamaz, akar.
 */

const PAD_L = 14;
const PAD_R = 58;
const AXIS_H = 20;

interface Props {
  quakes: Quake[];
  now: number;
  windowMs: number;
  windowKey: WindowKey;
  hoverId: string | null;
  selectedId: string | null;
  onHover: (id: string | null) => void;
  onSelect: (id: string) => void;
}

interface Mark {
  quake: Quake;
  x: number;
  amp: number;
  width: number;
}

function noise(n: number): number {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export default function Seismogram({ quakes, now, windowMs, windowKey, hoverId, selectedId, onHover, onSelect }: Props) {
  const wrap = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });

  useEffect(() => {
    const element = wrap.current!;
    const observer = new ResizeObserver(([entry]) => {
      setSize({ w: Math.round(entry.contentRect.width), h: Math.round(entry.contentRect.height) });
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const plotW = Math.max(1, size.w - PAD_L - PAD_R);
  const y0 = (size.h - AXIS_H) * 0.64;
  const maxAmp = (size.h - AXIS_H) * 0.58;
  const start = now - windowMs;

  const marks: Mark[] = useMemo(
    () =>
      quakes.map((quake) => ({
        quake,
        x: PAD_L + ((quakeTime(quake) - start) / windowMs) * plotW,
        amp: maxAmp * Math.min(1, Math.max(0.015, ((quake.mag - 0.5) / 6) ** 1.8)),
        width: 5 + quake.mag * 5,
      })),
    [quakes, start, windowMs, plotW, maxAmp],
  );

  useEffect(() => {
    const element = canvas.current;
    if (!element || size.w === 0) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    element.width = size.w * dpr;
    element.height = size.h * dpr;
    const ctx = element.getContext('2d')!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, size.w, size.h);

    const line = cssVar('--line');
    const text3 = cssVar('--text-3');
    const trace = cssVar('--trace');
    const signal = cssVar('--signal');
    const mono = cssVar('--mono');

    // Eksen ve ızgara
    ctx.font = `10px ${mono}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';
    for (const tick of axisTicks(start, now, windowKey)) {
      const x = PAD_L + ((tick.t - start) / windowMs) * plotW;
      ctx.strokeStyle = line;
      ctx.globalAlpha = tick.major ? 1 : 0.55;
      ctx.beginPath();
      ctx.moveTo(Math.round(x) + 0.5, 6);
      ctx.lineTo(Math.round(x) + 0.5, size.h - AXIS_H + 2);
      ctx.stroke();
      ctx.globalAlpha = 1;
      if (x > PAD_L + 14 && x < size.w - PAD_R - 14) {
        ctx.fillStyle = text3;
        ctx.fillText(tick.label, x, size.h - 6);
      }
    }

    // İz: taban gürültüsü + her depremin sönümlü dalgası
    const n = Math.ceil(plotW * dpr);
    const amp = new Float32Array(n + 1);
    const bucket = windowMs / 640;
    for (let i = 0; i <= n; i++) {
      const b = (start + (i / n) * windowMs) / bucket;
      const f = Math.floor(b);
      const v = noise(f) + (noise(f + 1) - noise(f)) * (b - f);
      amp[i] = (v - 0.5) * 1.8;
    }
    for (const mark of marks) {
      const i0 = Math.max(0, Math.floor((mark.x - PAD_L - 3) * dpr));
      const i1 = Math.min(n, Math.ceil((mark.x - PAD_L + mark.width) * dpr));
      for (let i = i0; i <= i1; i++) {
        const dx = PAD_L + i / dpr - mark.x;
        const envelope = dx < 0 ? Math.max(0, 1 + dx / 3) * 0.4 : Math.exp(-dx / (mark.width / 3.4));
        amp[i] += mark.amp * envelope * Math.sin(dx * 1.4 + 0.6);
      }
    }
    const traceSegment = (from: number, to: number) => {
      ctx.beginPath();
      for (let i = from; i <= to; i++) {
        const x = PAD_L + i / dpr;
        const y = y0 - amp[i];
        if (i === from) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    };
    ctx.lineJoin = 'round';
    ctx.lineWidth = 1;
    ctx.strokeStyle = trace;
    traceSegment(0, n);

    // Belirgin depremler kendi renginde
    ctx.lineWidth = 1.3;
    const notable = marks.filter((m) => m.quake.mag >= 2.5).sort((a, b) => a.quake.mag - b.quake.mag);
    for (const mark of notable) {
      ctx.strokeStyle = magColor(mark.quake.mag);
      const i0 = Math.max(0, Math.floor((mark.x - PAD_L - 3) * dpr));
      const i1 = Math.min(n, Math.ceil((mark.x - PAD_L + mark.width) * dpr));
      traceSegment(i0, i1);
    }

    // En büyüklerin etiketleri, birbirinin üstüne binmeden
    ctx.font = `500 10px ${mono}`;
    ctx.textAlign = 'center';
    const placed: number[] = [];
    for (const mark of [...notable].reverse()) {
      if (mark.quake.mag < 3.5 || placed.length >= 8) break;
      if (placed.some((x) => Math.abs(x - mark.x) < 34)) continue;
      placed.push(mark.x);
      ctx.fillStyle = magColor(mark.quake.mag);
      ctx.fillText(fmtMag(mark.quake.mag), mark.x + 2, Math.max(12, y0 - mark.amp - 8));
    }

    // Seçili / üzerinde durulan deprem
    const highlight = (id: string | null, dashed: boolean) => {
      const mark = id ? marks.find((m) => m.quake.id === id) : undefined;
      if (!mark) return;
      ctx.save();
      ctx.strokeStyle = cssVar('--text');
      ctx.globalAlpha = dashed ? 0.45 : 0.8;
      ctx.setLineDash(dashed ? [3, 3] : []);
      ctx.beginPath();
      ctx.moveTo(Math.round(mark.x) + 0.5, 4);
      ctx.lineTo(Math.round(mark.x) + 0.5, size.h - AXIS_H);
      ctx.stroke();
      ctx.restore();
    };
    highlight(selectedId, false);
    if (hoverId !== selectedId) highlight(hoverId, true);

    // Şimdi çizgisi
    const xNow = PAD_L + plotW;
    ctx.strokeStyle = signal;
    ctx.globalAlpha = 0.5;
    ctx.setLineDash([2, 3]);
    ctx.beginPath();
    ctx.moveTo(xNow + 0.5, 4);
    ctx.lineTo(xNow + 0.5, size.h - AXIS_H);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
    ctx.fillStyle = signal;
    ctx.font = `500 9px ${mono}`;
    ctx.textAlign = 'left';
    ctx.fillText('ŞİMDİ', xNow + 9, y0 + 3);
  }, [marks, size, now, start, windowMs, windowKey, plotW, y0, hoverId, selectedId]);

  const pick = (clientX: number): Mark | undefined => {
    const left = wrap.current!.getBoundingClientRect().left;
    const x = clientX - left;
    let best: Mark | undefined;
    let bestScore = Infinity;
    for (const mark of marks) {
      const distance = Math.abs(mark.x - x);
      if (distance > 10) continue;
      const score = distance - mark.quake.mag * 1.6; // yakın ve büyük olan kazanır
      if (score < bestScore) {
        bestScore = score;
        best = mark;
      }
    }
    return best;
  };

  const hovered = hoverId ? marks.find((m) => m.quake.id === hoverId) : undefined;

  return (
    <div
      ref={wrap}
      className="seis"
      onMouseMove={(event) => onHover(pick(event.clientX)?.quake.id ?? null)}
      onMouseLeave={() => onHover(null)}
      onClick={(event) => {
        const mark = pick(event.clientX);
        if (mark) onSelect(mark.quake.id);
      }}
    >
      <canvas ref={canvas} className="seis__canvas" aria-hidden="true" />
      <span className="seis__label">Sismogram · {WINDOWS[windowKey].label}</span>
      <span className="seis__pen" style={{ left: PAD_L + plotW, top: y0 }} aria-hidden="true" />
      {hovered && (
        <div className="seis__tip" style={{ left: Math.min(Math.max(hovered.x, 90), size.w - 120) }}>
          <b style={{ color: magColor(hovered.quake.mag) }}>{fmtMag(hovered.quake.mag)}</b>
          <span>{splitLocation(hovered.quake).title}</span>
          <span className="seis__tip-time">{relative(quakeTime(hovered.quake), now)}</span>
        </div>
      )}
    </div>
  );
}

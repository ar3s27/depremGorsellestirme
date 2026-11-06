import type { Quake } from '../api';
import { fmtMag, magColor, splitLocation } from '../format';

export interface Toast {
  key: number;
  quake: Quake;
}

export default function Toasts({ toasts, onOpen, onDismiss }: { toasts: Toast[]; onOpen: (id: string) => void; onDismiss: (key: number) => void }) {
  return (
    <div className="toasts" aria-live="polite">
      {toasts.map(({ key, quake }) => (
        <button
          key={key}
          className="toast"
          style={{ '--c': magColor(quake.mag) } as React.CSSProperties}
          onClick={() => {
            onOpen(quake.id);
            onDismiss(key);
          }}
        >
          <span className="toast__label">Yeni deprem</span>
          <span className="toast__body">
            <b>{fmtMag(quake.mag)}</b> {splitLocation(quake).title}
          </span>
        </button>
      ))}
    </div>
  );
}

import type { LayerSpecification, StyleSpecification } from 'maplibre-gl';

/** OpenFreeMap'in anahtarsız "dark" altlığı, Sismik renklerine boyanır. */
const STYLE_URL = 'https://tiles.openfreemap.org/styles/dark';

export const C = {
  land: '#15120f',
  landAlt: '#191512',
  water: '#0a1114',
  road: '#231e1a',
  roadMajor: '#2b241f',
  border: '#5b4a3d',
  province: '#2f2722',
  label: '#8f857a',
  labelStrong: '#b5a99c',
  labelWater: '#35505a',
  halo: '#0e0c0b',
};

// Gürültü yapan katmanlar: binalar, havalimanı, demiryolu, yol adları ve tek yön okları.
const DROP = /^(building|aeroway|railway|road_oneway|highway_name|road_area_pier|road_pier|landcover_ice|landcover_glacier)/;

function paint(layer: LayerSpecification): void {
  const id = layer.id;
  const p = ((layer as { paint?: Record<string, unknown> }).paint ??= {});
  if (layer.type === 'background') p['background-color'] = C.land;
  else if (id === 'water') p['fill-color'] = C.water;
  else if (id === 'waterway') p['line-color'] = C.water;
  else if (layer.type === 'fill') p['fill-color'] = C.landAlt;
  else if (id.startsWith('boundary_country')) p['line-color'] = C.border;
  else if (id.startsWith('boundary_state')) p['line-color'] = C.province;
  else if (id.startsWith('highway_major') || id.startsWith('highway_motorway')) p['line-color'] = C.roadMajor;
  else if (id.startsWith('highway')) p['line-color'] = C.road;
  else if (id === 'water_name') {
    p['text-color'] = C.labelWater;
    p['text-halo-color'] = C.water;
  } else if (layer.type === 'symbol') {
    p['text-color'] = /city_large|country|state/.test(id) ? C.labelStrong : C.label;
    p['text-halo-color'] = C.halo;
    p['text-halo-width'] = 1.2;
  }
  // Yer adları Türkçe; yoksa Latin harfli ad (Kiril/Arap yazısı yerine).
  const layout = (layer as { layout?: Record<string, unknown> }).layout;
  if (layout && JSON.stringify(layout['text-field'] ?? '').includes('"name')) layout['text-field'] = NAME;
  // Şehir noktası gibi simgeler hem sade görünüme uymuyor hem de koyu stilin sprite'ında yok.
  if (layout) delete layout['icon-image'];
}

const NAME = ['coalesce', ['get', 'name:tr'], ['get', 'name:latin'], ['get', 'name_en'], ['get', 'name']];

export function restyle(style: StyleSpecification): StyleSpecification {
  const layers = style.layers.filter((layer) => !DROP.test(layer.id));
  layers.forEach(paint);
  // Natural Earth gölgeli rölyefi: dağlara doku, renksiz ve hafif.
  if (style.sources.ne2_shaded) {
    const at = layers.findIndex((layer) => layer.type === 'background') + 1;
    layers.splice(at, 0, {
      id: 'relief',
      type: 'raster',
      source: 'ne2_shaded',
      maxzoom: 8,
      paint: {
        'raster-opacity': 0.2,
        'raster-saturation': -1,
        'raster-contrast': 0.25,
        'raster-brightness-max': 0.6,
      },
    });
  }
  return { ...style, layers };
}

export async function loadBaseStyle(signal?: AbortSignal): Promise<StyleSpecification> {
  const response = await fetch(STYLE_URL, { signal });
  if (!response.ok) throw new Error(`Harita altlığı: HTTP ${response.status}`);
  return restyle((await response.json()) as StyleSpecification);
}

/** Altlık yüklenemezse depremler yine düz zemin üzerinde gösterilir. */
export const FALLBACK_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'background', type: 'background', paint: { 'background-color': C.land } }],
};

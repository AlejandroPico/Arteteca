import type { Catalogo, ObraDetalle, ObraResumen } from './types';

const base = import.meta.env.BASE_URL;

function resolveAsset(path: string): string {
  if (/^(?:https?:)?\/\//.test(path) || path.startsWith('data:')) return path;
  return `${base}${path.replace(/^\/+/, '')}`;
}

function resolveSummary(work: ObraResumen): ObraResumen {
  return {
    ...work,
    imagen: { ...work.imagen, src: resolveAsset(work.imagen.src) },
  };
}

export async function loadCatalog(): Promise<Catalogo> {
  const response = await fetch(`${base}data/catalogo.json`, { cache: 'no-cache' });
  if (!response.ok) throw new Error(`No se pudo cargar el catálogo (${response.status})`);
  const catalog = (await response.json()) as Catalogo;
  return { ...catalog, obras: catalog.obras.map(resolveSummary) };
}

export async function loadArtwork(id: string): Promise<ObraDetalle> {
  const response = await fetch(`${base}data/obras/${encodeURIComponent(id)}.json`);
  if (!response.ok) throw new Error(`No se pudo cargar la ficha (${response.status})`);
  const detail = (await response.json()) as ObraDetalle;
  return {
    ...detail,
    imagen: { ...detail.imagen, src: resolveAsset(detail.imagen.src) },
  };
}

export function normalizeForSearch(value: string): string {
  return value
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLocaleLowerCase('es')
    .trim();
}

export function shuffle<T>(items: T[]): T[] {
  const result = [...items];
  const random = new Uint32Array(result.length);
  crypto.getRandomValues(random);
  for (let index = result.length - 1; index > 0; index -= 1) {
    const target = random[index] % (index + 1);
    [result[index], result[target]] = [result[target], result[index]];
  }
  return result;
}

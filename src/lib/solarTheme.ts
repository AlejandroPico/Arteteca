import type { Tema } from './types';

export type ThemePeriod = 'morning' | 'afternoon' | 'night';
export type ThemeSource = 'solar' | 'local-time' | 'manual';

export interface ThemeCoordinates {
  latitude: number;
  longitude: number;
}

export interface ResolvedTheme {
  mode: Tema;
  period: ThemePeriod;
  baseTheme: 'claro' | 'oscuro';
  source: ThemeSource;
  solarAltitude: number | null;
}

interface StoredCoordinates extends ThemeCoordinates {
  savedAt: number;
}

const THEME_KEY = 'arteteca-tema';
const COORDINATES_KEY = 'arteteca-coordenadas-solares';
const COORDINATE_MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000;
const CIVIL_TWILIGHT_DEGREES = -6;
const DAY_MS = 86_400_000;
const J2000_MS = Date.UTC(2000, 0, 1, 12);

function degreesToRadians(value: number): number {
  return value * Math.PI / 180;
}

function radiansToDegrees(value: number): number {
  return value * 180 / Math.PI;
}

function normalizeDegrees(value: number): number {
  return ((value % 360) + 360) % 360;
}

function normalizeRadians(value: number): number {
  const circle = Math.PI * 2;
  return ((value + Math.PI) % circle + circle) % circle - Math.PI;
}

function solarGeometry(date: Date, coordinates: ThemeCoordinates): { altitude: number; hourAngle: number } {
  const daysSinceJ2000 = (date.getTime() - J2000_MS) / DAY_MS;
  const meanLongitude = normalizeDegrees(280.46 + 0.9856474 * daysSinceJ2000);
  const meanAnomaly = degreesToRadians(normalizeDegrees(357.528 + 0.9856003 * daysSinceJ2000));
  const eclipticLongitude = degreesToRadians(normalizeDegrees(
    meanLongitude + 1.915 * Math.sin(meanAnomaly) + 0.02 * Math.sin(2 * meanAnomaly),
  ));
  const obliquity = degreesToRadians(23.439 - 0.0000004 * daysSinceJ2000);
  const rightAscension = Math.atan2(
    Math.cos(obliquity) * Math.sin(eclipticLongitude),
    Math.cos(eclipticLongitude),
  );
  const declination = Math.asin(Math.sin(obliquity) * Math.sin(eclipticLongitude));
  const siderealDegrees = normalizeDegrees(
    (18.697374558 + 24.06570982441908 * daysSinceJ2000) * 15 + coordinates.longitude,
  );
  const hourAngle = normalizeRadians(degreesToRadians(siderealDegrees) - rightAscension);
  const latitude = degreesToRadians(coordinates.latitude);
  const altitude = Math.asin(
    Math.sin(latitude) * Math.sin(declination) +
      Math.cos(latitude) * Math.cos(declination) * Math.cos(hourAngle),
  );

  return { altitude: radiansToDegrees(altitude), hourAngle };
}

function fallbackPeriod(date: Date): ThemePeriod {
  const hour = date.getHours() + date.getMinutes() / 60;
  if (hour >= 5.5 && hour < 13) return 'morning';
  if (hour >= 13 && hour < 20.5) return 'afternoon';
  return 'night';
}

export function resolveAutomaticPeriod(date: Date, coordinates: ThemeCoordinates | null): ResolvedTheme {
  if (!coordinates) {
    const period = fallbackPeriod(date);
    return {
      mode: 'auto',
      period,
      baseTheme: period === 'night' ? 'oscuro' : 'claro',
      source: 'local-time',
      solarAltitude: null,
    };
  }

  const { altitude, hourAngle } = solarGeometry(date, coordinates);
  const period: ThemePeriod = altitude < CIVIL_TWILIGHT_DEGREES
    ? 'night'
    : hourAngle < 0
      ? 'morning'
      : 'afternoon';

  return {
    mode: 'auto',
    period,
    baseTheme: period === 'night' ? 'oscuro' : 'claro',
    source: 'solar',
    solarAltitude: altitude,
  };
}

export function resolveTheme(mode: Tema, date = new Date(), coordinates: ThemeCoordinates | null = null): ResolvedTheme {
  if (mode === 'auto') return resolveAutomaticPeriod(date, coordinates);

  return {
    mode,
    period: mode === 'oscuro' ? 'night' : 'afternoon',
    baseTheme: mode,
    source: 'manual',
    solarAltitude: null,
  };
}

export function applyThemeToDocument(
  mode: Tema,
  date = new Date(),
  coordinates: ThemeCoordinates | null = null,
): ResolvedTheme {
  const resolved = resolveTheme(mode, date, coordinates);
  const root = document.documentElement;
  root.dataset.theme = resolved.baseTheme;
  root.dataset.themeMode = resolved.mode;
  root.dataset.themePeriod = resolved.period;
  root.dataset.themeSource = resolved.source;

  if (resolved.solarAltitude === null) delete root.dataset.sunAltitude;
  else root.dataset.sunAltitude = resolved.solarAltitude.toFixed(1);

  const themeColor = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
  if (themeColor) {
    themeColor.content = resolved.period === 'night'
      ? '#121416'
      : resolved.period === 'morning'
        ? '#edf1ee'
        : '#f0ede6';
  }

  return resolved;
}

export function readStoredTheme(): Tema {
  try {
    const value = localStorage.getItem(THEME_KEY);
    return value === 'claro' || value === 'oscuro' || value === 'auto' ? value : 'auto';
  } catch (_) {
    return 'auto';
  }
}

export function storeTheme(theme: Tema): void {
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch (_) {}
}

export function readStoredCoordinates(now = Date.now()): ThemeCoordinates | null {
  try {
    const value = JSON.parse(localStorage.getItem(COORDINATES_KEY) ?? 'null') as StoredCoordinates | null;
    if (
      !value ||
      !Number.isFinite(value.latitude) ||
      !Number.isFinite(value.longitude) ||
      !Number.isFinite(value.savedAt) ||
      now - value.savedAt > COORDINATE_MAX_AGE_MS
    ) {
      return null;
    }
    return { latitude: value.latitude, longitude: value.longitude };
  } catch (_) {
    return null;
  }
}

export function storeCoordinates(coordinates: ThemeCoordinates): ThemeCoordinates {
  const reduced = {
    latitude: Number(coordinates.latitude.toFixed(3)),
    longitude: Number(coordinates.longitude.toFixed(3)),
  };
  try {
    const stored: StoredCoordinates = { ...reduced, savedAt: Date.now() };
    localStorage.setItem(COORDINATES_KEY, JSON.stringify(stored));
  } catch (_) {}
  return reduced;
}

export function themePeriodLabel(period: ThemePeriod): string {
  if (period === 'morning') return 'mañana';
  if (period === 'afternoon') return 'tarde';
  return 'noche';
}

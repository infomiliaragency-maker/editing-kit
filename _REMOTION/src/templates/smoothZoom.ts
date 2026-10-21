/**
 * ZOOM SMOOTH SUI JUMP CUT
 * A ogni taglio lo zoom non scatta: parte dal valore del segmento precedente e arriva
 * al nuovo con una curva bezier ease-in-out. Dentro il segmento c'è un push-in lentissimo.
 */
import { Easing, interpolate } from "remotion";

export type Segment = { start: number; end: number };

// Curva di velocità dello zoom (stile "ease in-out" di Premiere/AE)
export const ZOOM_CURVE = Easing.bezier(0.65, 0, 0.35, 1);

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const smoothZoom = (
  t: number,
  segments: Segment[],
  { levels = [1.0, 1.12], rampS = 0.6, driftPerSecond = 0.006 } = {},
) => {
  const i = Math.max(0, segments.findIndex((s) => t >= s.start && t < s.end));
  const seg = segments[i] ?? segments[0];
  const level = (k: number) => levels[k % levels.length];
  const target = level(i);
  const prev = i > 0 ? level(i - 1) : target;
  const ramp = interpolate(t, [seg.start, seg.start + rampS], [prev, target], { ...clamp, easing: ZOOM_CURVE });
  const drift = (t - seg.start) * driftPerSecond;
  return ramp + drift;
};

import type { Point } from "./types";

/** Keep the entire node card inside logical canvas coordinates (independent of pan/zoom). */
export function clampNodePosition(
  position: Point,
  canvasWidth: number,
  canvasHeight: number,
  nodeWidth: number,
  nodeHeight: number,
): Point {
  const safeDimension = (value: number) => Number.isFinite(value) ? Math.max(0, value) : 0;
  const maxX = Math.max(0, safeDimension(canvasWidth) - safeDimension(nodeWidth));
  const maxY = Math.max(0, safeDimension(canvasHeight) - safeDimension(nodeHeight));
  const x = Number.isFinite(position.x) ? position.x : 0;
  const y = Number.isFinite(position.y) ? position.y : 0;
  return {
    x: Math.min(maxX, Math.max(0, x)),
    y: Math.min(maxY, Math.max(0, y)),
  };
}

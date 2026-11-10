import type { Point } from "./types";

/** Keep the entire node card inside logical canvas coordinates (independent of pan/zoom). */
export function clampNodePosition(
  position: Point,
  canvasWidth: number,
  canvasHeight: number,
  nodeWidth: number,
  nodeHeight: number,
): Point {
  const maxX = Math.max(0, canvasWidth - nodeWidth);
  const maxY = Math.max(0, canvasHeight - nodeHeight);
  return {
    x: Math.min(maxX, Math.max(0, position.x)),
    y: Math.min(maxY, Math.max(0, position.y)),
  };
}

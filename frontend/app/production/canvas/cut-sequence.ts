import type { CanvasNode } from "./types";

// Follow only explicit CUT predecessor references; never infer order from array position.
// A missing reference is not proof of a valid sequence and is handled by the caller.
export function hasPredecessorCycle(startId: string, nodes: readonly CanvasNode[]): boolean {
  const byId = new Map(nodes.filter((node) => node.kind === "CUT").map((node) => [node.id, node]));
  const visited = new Set<string>();
  let currentId: string | undefined = startId;
  while (currentId) {
    if (visited.has(currentId)) return true;
    visited.add(currentId);
    const node = byId.get(currentId);
    if (!node) return false;
    currentId = node.cutDetails?.previousCutId?.trim() || undefined;
  }
  return false;
}

/**
 * A predecessor ID that does not resolve to a CUT is a broken reference.
 * A cycle is handled independently by hasPredecessorCycle.
 */
export function hasBrokenPredecessorReference(startId: string, nodes: readonly CanvasNode[]): boolean {
  const byId = new Map(nodes.filter((node) => node.kind === "CUT").map((node) => [node.id, node]));
  const visited = new Set<string>();
  let currentId: string | undefined = startId;
  while (currentId) {
    if (visited.has(currentId)) return false;
    visited.add(currentId);
    const node = byId.get(currentId);
    if (!node) return true;
    currentId = node.cutDetails?.previousCutId?.trim() || undefined;
  }
  return false;
}

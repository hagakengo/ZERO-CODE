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

/**
 * Every reachable predecessor must belong to the selected CUT's scope,
 * scene and script. Missing references and cycles are separate blockers.
 */
export function hasInconsistentPredecessorContext(startId: string, nodes: readonly CanvasNode[]): boolean {
  const byId = new Map(nodes.filter((node) => node.kind === "CUT").map((node) => [node.id, node]));
  const selected = byId.get(startId);
  if (!selected) return true;
  const scope = selected.projectScope;
  const scene = selected.cutDetails?.sceneId;
  const script = selected.cutDetails?.scriptId;
  if (!scope || scope === "UNVERIFIED" || !scene?.trim() || !script?.trim()) return true;
  const visited = new Set<string>();
  let currentId: string | undefined = startId;
  while (currentId) {
    if (visited.has(currentId)) return false;
    visited.add(currentId);
    const node = byId.get(currentId);
    if (!node) return false;
    if (node.projectScope !== scope || node.cutDetails?.sceneId !== scene || node.cutDetails?.scriptId !== script) return true;
    currentId = node.cutDetails?.previousCutId?.trim() || undefined;
  }
  return false;
}

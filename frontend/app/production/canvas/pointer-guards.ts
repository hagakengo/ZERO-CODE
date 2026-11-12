/** A single primary left-button pointer may own the Canvas interaction. */
export function canBeginPointerInteraction(isPrimary: boolean, button: number, hasActiveInteraction: boolean): boolean {
  return isPrimary && button === 0 && !hasActiveInteraction;
}

/** Ignore termination events from pointers that do not own the interaction. */
export function isActivePointer(activePointerId: number | null, eventPointerId: number): boolean {
  return activePointerId !== null && activePointerId === eventPointerId;
}

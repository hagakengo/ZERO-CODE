import type { Point } from "./types";

export const KEYBOARD_MOVE_STEP = 16;

// Return null for browser-native arrow keys and unsupported modifier combinations.
export function keyboardMoveDelta(key: string, altKey: boolean, ctrlKey: boolean, metaKey: boolean, shiftKey: boolean): Point | null {
  if (!altKey || ctrlKey || metaKey || shiftKey) return null;
  switch (key) {
    case "ArrowLeft": return { x: -KEYBOARD_MOVE_STEP, y: 0 };
    case "ArrowRight": return { x: KEYBOARD_MOVE_STEP, y: 0 };
    case "ArrowUp": return { x: 0, y: -KEYBOARD_MOVE_STEP };
    case "ArrowDown": return { x: 0, y: KEYBOARD_MOVE_STEP };
    default: return null;
  }
}

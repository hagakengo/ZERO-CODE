import type { PointerEvent as ReactPointerEvent } from "react";
import { NODE_HEIGHT, NODE_WIDTH, statusClasses } from "./test-data";
import type { CanvasNode, Point } from "./types";

type Props = {
  node: CanvasNode;
  position: Point;
  selected: boolean;
  onPointerDown: (event: ReactPointerEvent<HTMLButtonElement>, node: CanvasNode) => void;
  onSelect: (nodeId: string) => void;
};

export function CanvasNodeCard({ node, position, selected, onPointerDown, onSelect }: Props) {
  return (
    <button
      type="button"
      data-node-id={node.id}
      aria-pressed={selected}
      onClick={() => onSelect(node.id)}
      onPointerDown={(event) => onPointerDown(event, node)}
      className={`absolute cursor-grab rounded-xl border bg-[#0b1018] p-3 text-left shadow-lg active:cursor-grabbing focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300 ${selected ? "border-cyan-400 bg-cyan-400/10" : "border-white/15 hover:border-white/40"}`}
      style={{ left: position.x, top: position.y, width: NODE_WIDTH, height: NODE_HEIGHT, touchAction: "none" }}
    >
      <span className="text-xs tracking-wider text-cyan-300">{node.kind}</span>
      <span className="mt-1 block truncate font-medium">{node.title}</span>
      <span className={`mt-2 inline-block rounded border px-2 py-1 text-[11px] ${statusClasses[node.status]}`}>{node.status}</span>
    </button>
  );
}

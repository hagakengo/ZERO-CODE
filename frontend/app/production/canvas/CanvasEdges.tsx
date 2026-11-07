import { CANVAS_HEIGHT, CANVAS_WIDTH, NODE_HEIGHT, NODE_WIDTH } from "./test-data";
import type { CanvasEdge, CanvasNode, Point } from "./types";

type Props = {
  edges: readonly CanvasEdge[];
  nodes: readonly CanvasNode[];
  positions: Readonly<Record<string, Point>>;
};

export function CanvasEdges({ edges, nodes, positions }: Props) {
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));
  return (
    <svg aria-label="検証用ノード接続線" className="pointer-events-none absolute inset-0" width={CANVAS_WIDTH} height={CANVAS_HEIGHT} viewBox={`0 0 ${CANVAS_WIDTH} ${CANVAS_HEIGHT}`}>
      <defs>
        <marker id="canvas-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
          <path d="M0,0 L8,4 L0,8 z" fill="rgb(34 211 238 / 0.7)" />
        </marker>
      </defs>
      {edges.map((edge) => {
        const source = nodeMap.get(edge.source);
        const target = nodeMap.get(edge.target);
        if (!source || !target) return null;
        const from = positions[source.id] ?? source.initialPosition;
        const to = positions[target.id] ?? target.initialPosition;
        const x1 = from.x + NODE_WIDTH;
        const y1 = from.y + NODE_HEIGHT / 2;
        const x2 = to.x;
        const y2 = to.y + NODE_HEIGHT / 2;
        const bend = Math.max(40, Math.abs(x2 - x1) * 0.45);
        const path = `M ${x1} ${y1} C ${x1 + bend} ${y1}, ${x2 - bend} ${y2}, ${x2} ${y2}`;
        return <path key={edge.id} data-edge-id={edge.id} d={path} fill="none" stroke="rgb(34 211 238 / 0.55)" strokeWidth="2" markerEnd="url(#canvas-arrow)" />;
      })}
    </svg>
  );
}

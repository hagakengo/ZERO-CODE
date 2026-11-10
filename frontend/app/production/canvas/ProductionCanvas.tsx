"use client";

import { useMemo, useRef, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent, PointerEvent as ReactPointerEvent } from "react";
import { CanvasEdges } from "./CanvasEdges";
import { CanvasNodeCard } from "./CanvasNodeCard";
import { NodeDetails } from "./NodeDetails";
import { clampNodePosition } from "./node-bounds";
import { keyboardMoveDelta } from "./keyboard-controls";
import { CANVAS_HEIGHT, CANVAS_WIDTH, NODE_HEIGHT, NODE_WIDTH, kindLabels, sampleEdges, sampleNodes } from "./test-data";
import type { CanvasNode, Point } from "./types";

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 2;
const ZOOM_STEP = 0.2;

type Interaction =
  | { kind: "node"; pointerId: number; nodeId: string; startClient: Point; startPosition: Point }
  | { kind: "pan"; pointerId: number; startClient: Point; startPan: Point }
  | null;

const initialPositions = Object.fromEntries(sampleNodes.map((node) => [node.id, node.initialPosition])) as Record<string, Point>;

function clampZoom(value: number) {
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Number(value.toFixed(2))));
}

export function ProductionCanvas() {
  const [selectedId, setSelectedId] = useState(sampleNodes[0].id);
  const [positions, setPositions] = useState<Record<string, Point>>(() => ({ ...initialPositions }));
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<Point>({ x: 18, y: 18 });
  const interaction = useRef<Interaction>(null);

  const selected = sampleNodes.find((node) => node.id === selectedId) ?? sampleNodes[0];
  const related = useMemo(() => sampleEdges.filter((edge) => edge.source === selected.id || edge.target === selected.id), [selected.id]);

  function beginNodeDrag(event: ReactPointerEvent<HTMLButtonElement>, node: CanvasNode) {
    event.stopPropagation();
    event.currentTarget.setPointerCapture(event.pointerId);
    setSelectedId(node.id);
    interaction.current = {
      kind: "node",
      pointerId: event.pointerId,
      nodeId: node.id,
      startClient: { x: event.clientX, y: event.clientY },
      startPosition: positions[node.id] ?? node.initialPosition,
    };
  }

  function beginPan(event: ReactPointerEvent<HTMLDivElement>) {
    if (event.target !== event.currentTarget) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    interaction.current = { kind: "pan", pointerId: event.pointerId, startClient: { x: event.clientX, y: event.clientY }, startPan: pan };
  }

  function moveInteraction(event: ReactPointerEvent<HTMLDivElement>) {
    const active = interaction.current;
    if (!active || active.pointerId !== event.pointerId) return;
    const dx = event.clientX - active.startClient.x;
    const dy = event.clientY - active.startClient.y;
    if (active.kind === "node") {
      setPositions((current) => ({
        ...current,
        [active.nodeId]: clampNodePosition(
          { x: active.startPosition.x + dx / zoom, y: active.startPosition.y + dy / zoom },
          CANVAS_WIDTH, CANVAS_HEIGHT, NODE_WIDTH, NODE_HEIGHT,
        ),
      }));
    } else {
      setPan({ x: active.startPan.x + dx, y: active.startPan.y + dy });
    }
  }

  function endInteraction(event: ReactPointerEvent<HTMLDivElement>) {
    if (interaction.current?.pointerId === event.pointerId) interaction.current = null;
  }

  function moveNodeByKeyboard(event: ReactKeyboardEvent<HTMLButtonElement>, node: CanvasNode) {
    const delta = keyboardMoveDelta(event.key, event.altKey, event.ctrlKey, event.metaKey, event.shiftKey);
    if (!delta) return;
    event.preventDefault();
    event.stopPropagation();
    setSelectedId(node.id);
    setPositions((current) => {
      const position = current[node.id] ?? node.initialPosition;
      return {
        ...current,
        [node.id]: clampNodePosition(
          { x: position.x + delta.x, y: position.y + delta.y },
          CANVAS_WIDTH, CANVAS_HEIGHT, NODE_WIDTH, NODE_HEIGHT,
        ),
      };
    });
  }

  function panByKeyboard(event: ReactKeyboardEvent<HTMLDivElement>) {
    if (event.target !== event.currentTarget) return;
    const delta = keyboardMoveDelta(event.key, event.altKey, event.ctrlKey, event.metaKey, event.shiftKey);
    if (!delta) return;
    event.preventDefault();
    setPan((current) => ({ x: current.x + delta.x, y: current.y + delta.y }));
  }

  // Explicit buttons work when browser or OS reserves Alt+arrow shortcuts.
  function moveSelectedNode(direction: "ArrowLeft" | "ArrowRight" | "ArrowUp" | "ArrowDown") {
    const delta = keyboardMoveDelta(direction, true, false, false, false);
    if (!delta) return;
    setPositions((current) => {
      const position = current[selected.id] ?? selected.initialPosition;
      return {
        ...current,
        [selected.id]: clampNodePosition(
          { x: position.x + delta.x, y: position.y + delta.y },
          CANVAS_WIDTH, CANVAS_HEIGHT, NODE_WIDTH, NODE_HEIGHT,
        ),
      };
    });
  }

  function panWithButton(direction: "ArrowLeft" | "ArrowRight" | "ArrowUp" | "ArrowDown") {
    const delta = keyboardMoveDelta(direction, true, false, false, false);
    if (!delta) return;
    setPan((current) => ({ x: current.x + delta.x, y: current.y + delta.y }));
  }

  function resetView() {
    setPositions({ ...initialPositions });
    setPan({ x: 18, y: 18 });
    setZoom(1);
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[210px_minmax(0,1fr)_320px]">
      <nav aria-label="検証用ノード一覧" className="rounded-xl border border-white/10 bg-[#10151c] p-4">
        <h2 className="mb-3 text-sm font-semibold">構成ツリー</h2>
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-1">
          {sampleNodes.map((node) => (
            <button key={node.id} type="button" onClick={() => setSelectedId(node.id)} aria-current={selected.id === node.id ? "true" : undefined} className={`rounded-lg border p-3 text-left text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300 ${selected.id === node.id ? "border-cyan-400 bg-cyan-400/10" : "border-white/10 hover:border-white/30"}`}>
              <span className="block text-xs text-slate-400">{kindLabels[node.kind]}</span>
              <span className="mt-1 block font-medium">{node.title}</span>
            </button>
          ))}
        </div>
      </nav>

      <section aria-label="検証用関係キャンバス" className="min-w-0 rounded-xl border border-white/10 bg-[#10151c] p-3">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div><h2 className="text-sm font-semibold">参照グラフ</h2><p className="mt-1 text-xs text-slate-400">ノードをドラッグ／背景をパン。キーボードは対象にフォーカスしてAlt＋矢印（16px刻み）。位置変更は保存されません。</p></div>
          <div className="flex items-center gap-2" aria-label="キャンバス表示倍率">
            <button type="button" aria-label="縮小" onClick={() => setZoom((value) => clampZoom(value - ZOOM_STEP))} className="rounded border border-white/15 px-3 py-2 text-sm hover:border-cyan-400">−</button>
            <output className="min-w-14 text-center text-xs text-slate-300">{Math.round(zoom * 100)}%</output>
            <button type="button" aria-label="拡大" onClick={() => setZoom((value) => clampZoom(value + ZOOM_STEP))} className="rounded border border-white/15 px-3 py-2 text-sm hover:border-cyan-400">＋</button>
            <button type="button" onClick={resetView} className="rounded border border-white/15 px-3 py-2 text-xs hover:border-cyan-400">RESET</button>
          </div>
        </div>
        <div className="mb-3 flex flex-wrap gap-3 text-xs">
          <div role="group" aria-label="選択中のノードを移動" className="flex flex-wrap items-center gap-1">
            <span className="mr-1 text-slate-300">選択ノードを移動</span>
            <button type="button" aria-label="選択ノードを左へ16px移動" onClick={() => moveSelectedNode("ArrowLeft")} className="rounded border border-white/20 px-2 py-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300">←</button>
            <button type="button" aria-label="選択ノードを上へ16px移動" onClick={() => moveSelectedNode("ArrowUp")} className="rounded border border-white/20 px-2 py-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300">↑</button>
            <button type="button" aria-label="選択ノードを下へ16px移動" onClick={() => moveSelectedNode("ArrowDown")} className="rounded border border-white/20 px-2 py-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300">↓</button>
            <button type="button" aria-label="選択ノードを右へ16px移動" onClick={() => moveSelectedNode("ArrowRight")} className="rounded border border-white/20 px-2 py-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300">→</button>
          </div>
          <div role="group" aria-label="キャンバス表示位置を移動" className="flex flex-wrap items-center gap-1">
            <span className="mr-1 text-slate-300">表示位置を移動</span>
            <button type="button" aria-label="表示位置を左へ16px移動" onClick={() => panWithButton("ArrowLeft")} className="rounded border border-white/20 px-2 py-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300">←</button>
            <button type="button" aria-label="表示位置を上へ16px移動" onClick={() => panWithButton("ArrowUp")} className="rounded border border-white/20 px-2 py-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300">↑</button>
            <button type="button" aria-label="表示位置を下へ16px移動" onClick={() => panWithButton("ArrowDown")} className="rounded border border-white/20 px-2 py-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300">↓</button>
            <button type="button" aria-label="表示位置を右へ16px移動" onClick={() => panWithButton("ArrowRight")} className="rounded border border-white/20 px-2 py-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300">→</button>
          </div>
        </div>
        <div
          data-canvas-background
          tabIndex={0}
          aria-label="キャンバス背景。Altと矢印キーで表示位置を移動"
          aria-keyshortcuts="Alt+ArrowUp Alt+ArrowDown Alt+ArrowLeft Alt+ArrowRight"
          onKeyDown={panByKeyboard}
          className="relative h-[560px] w-full cursor-move overflow-hidden rounded-lg border border-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300 bg-[#080c12] [background-image:radial-gradient(circle,rgba(148,163,184,0.2)_1px,transparent_1px)] [background-size:22px_22px]"
          style={{ touchAction: "none" }}
          onPointerDown={beginPan}
          onPointerMove={moveInteraction}
          onPointerUp={endInteraction}
          onPointerCancel={endInteraction}
        >
          <div className="pointer-events-none absolute left-0 top-0" style={{ width: CANVAS_WIDTH, height: CANVAS_HEIGHT, transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: "0 0" }}>
            <CanvasEdges edges={sampleEdges} nodes={sampleNodes} positions={positions} />
            {sampleNodes.map((node) => <div key={node.id} className="pointer-events-auto"><CanvasNodeCard node={node} position={positions[node.id] ?? node.initialPosition} selected={selected.id === node.id} onPointerDown={beginNodeDrag} onSelect={setSelectedId} onKeyboardMove={moveNodeByKeyboard} /></div>)}
          </div>
        </div>
      </section>

      <NodeDetails selected={selected} nodes={sampleNodes} related={related} onSelect={setSelectedId} />
    </div>
  );
}

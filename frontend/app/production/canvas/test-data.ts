import type { CanvasEdge, CanvasNode, CanvasNodeKind, CanvasStatus } from "./types";

export const CANVAS_WIDTH = 720;
export const CANVAS_HEIGHT = 620;
export const NODE_WIDTH = 176;
export const NODE_HEIGHT = 92;

export const sampleNodes: readonly CanvasNode[] = [
  { id: "test-script-01", kind: "SCRIPT", title: "検証用脚本", status: "DRAFT", sourceId: "TEST-SCRIPT-001", sourceVersion: "test-r01", description: "架空の脚本ノード。実際の正史や承認記録ではありません。", initialPosition: { x: 20, y: 46 } },
  { id: "test-scene-01", kind: "SCENE", title: "検証用シーン", status: "UNVERIFIED", sourceId: "TEST-SCENE-001", description: "構成と参照関係の表示確認にのみ使用します。", initialPosition: { x: 250, y: 46 } },
  { id: "test-cut-01", kind: "CUT", title: "検証用CUT 01", status: "HOLD", sourceId: "TEST-CUT-001", description: "人物動作を含むCUT詳細の表示確認用。", initialPosition: { x: 500, y: 46 }, cutDetails: { sceneId: "TEST-SCENE-001", scriptId: "TEST-SCRIPT-001", purpose: "人物の選択を画面で確認する検証用CUT", action: "検証用人物が立ち止まる（未承認・架空）", camera: "固定カメラ（検証値）", sound: "未確認", continuity: "前後CUTとの接続はHOLD", timing: "24fps / 72f / 3.0s（検証値）", qc: "HOLD" } },
  { id: "test-cut-02", kind: "CUT", title: "検証用CUT 02", status: "NOT_FOUND", sourceId: "TEST-CUT-002", description: "参照素材が未確認であることの表示確認用。未制作を意味しません。", initialPosition: { x: 500, y: 222 }, cutDetails: { sceneId: "TEST-SCENE-001", scriptId: "TEST-SCRIPT-001", purpose: "参照切れ表示の確認", action: "未確認", camera: "未確認", sound: "未確認", continuity: "参照先が見つからないためNOT_FOUND", timing: "未確認", qc: "NOT_FOUND" } },
  { id: "test-character-01", kind: "CHARACTER", title: "検証用キャラクター", status: "DRAFT", sourceId: "TEST-CHAR-001", sourceVersion: "test-r01", description: "実在のキャラクター設定・MASTERではありません。", initialPosition: { x: 250, y: 398 } },
  { id: "test-asset-01", kind: "ASSET", title: "検証用素材", status: "UNVERIFIED", sourceId: "TEST-ASSET-001", description: "実ファイルを読み込まない参照表示テストです。", initialPosition: { x: 20, y: 398 } },
] as const;

export const sampleEdges: readonly CanvasEdge[] = [
  { id: "edge-script-scene", source: "test-script-01", target: "test-scene-01", label: "CONTAINS", status: "DRAFT" },
  { id: "edge-scene-cut-01", source: "test-scene-01", target: "test-cut-01", label: "CONTAINS", status: "DRAFT" },
  { id: "edge-scene-cut-02", source: "test-scene-01", target: "test-cut-02", label: "CONTAINS", status: "UNVERIFIED" },
  { id: "edge-character-cut", source: "test-character-01", target: "test-cut-01", label: "APPEARS_IN", status: "UNVERIFIED" },
  { id: "edge-asset-cut", source: "test-asset-01", target: "test-cut-02", label: "REFERENCES", status: "UNVERIFIED" },
] as const;

export const kindLabels: Record<CanvasNodeKind, string> = {
  SCRIPT: "脚本", SCENE: "シーン", CUT: "カット", CHARACTER: "キャラクター", ASSET: "素材",
};

export const statusClasses: Record<CanvasStatus, string> = {
  DRAFT: "border-amber-400/40 text-amber-200",
  APPROVED: "border-emerald-400/40 text-emerald-200",
  HOLD: "border-orange-400/40 text-orange-200",
  NOT_FOUND: "border-rose-400/40 text-rose-200",
  UNVERIFIED: "border-slate-400/40 text-slate-200",
};

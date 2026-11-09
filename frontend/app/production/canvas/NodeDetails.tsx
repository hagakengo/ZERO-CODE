import { statusClasses } from "./test-data";
import { compareCutBoundaries } from "./continuity";
import { hasPredecessorCycle } from "./cut-sequence";
import type { ApprovalEvidence, CanvasEdge, CanvasNode, CutBoundaryState } from "./types";

type Props = {
  selected: CanvasNode;
  nodes: readonly CanvasNode[];
  related: readonly CanvasEdge[];
  onSelect: (nodeId: string) => void;
};

function Detail({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-xs text-slate-400">{label}</dt><dd className="mt-1 break-words">{value}</dd></div>;
}

const approvalFields = [
  ["脚本内容", "scriptContent"],
  ["統合ファイル", "integratedFile"],
  ["MASTER採用", "masterAdoption"],
  ["映像QC", "videoQc"],
] as const;

function evidenceText(evidence?: ApprovalEvidence): string {
  if (!evidence) return "UNVERIFIED（根拠未取得）";
  if (evidence.status === "APPROVED" && (!evidence.evidenceId?.trim() || !evidence.approvalScope?.trim())) {
    return "UNVERIFIED（APPROVED根拠不足）";
  }
  const details = [evidence.evidenceId, evidence.approvalScope].filter(Boolean);
  return details.length ? `${evidence.status} · ${details.join(" · ")}` : evidence.status;
}

function boundaryText(state?: CutBoundaryState): string {
  if (!state) return "UNVERIFIED（状態未記録）";
  const fields = [
    ["位置", state.characterPosition],
    ["姿勢", state.pose],
    ["向き", state.facing],
    ["小道具", state.props],
    ["カメラ", state.camera],
    ["根拠", state.evidenceId],
  ].filter((entry) => Boolean(entry[1]?.trim()));
  return fields.length ? fields.map(([label, value]) => `${label}: ${value}`).join(" / ") : "UNVERIFIED（状態未記録）";
}

export function NodeDetails({ selected, nodes, related, onSelect }: Props) {
  const cut = selected.cutDetails;
  // Only explicitly sourced predecessor links can establish a comparison candidate.
  const previousCut = cut?.previousCutId ? nodes.find((node) => node.id === cut.previousCutId && node.kind === "CUT") : undefined;
  const cycleDetected = cut ? hasPredecessorCycle(selected.id, nodes) : false;
  const sequenceVerified = Boolean(!cycleDetected && cut?.sequenceEvidenceId?.trim() && previousCut && previousCut.id !== selected.id && previousCut.cutDetails?.previousCutId !== selected.id && previousCut.cutDetails?.sceneId === cut.sceneId && previousCut.cutDetails?.scriptId === cut.scriptId);
  const sameVerifiedScope = previousCut?.projectScope && selected.projectScope && previousCut.projectScope === selected.projectScope && previousCut.projectScope !== "UNVERIFIED";
  const continuityCheck = sequenceVerified && sameVerifiedScope && previousCut && cut ? compareCutBoundaries(previousCut.cutDetails?.endState, cut.startState) : undefined;
  return (
    <aside aria-live="polite" aria-label="選択ノードの詳細" className="rounded-xl border border-white/10 bg-[#10151c] p-4">
      <h2 className="mb-4 text-sm font-semibold">ノード詳細</h2>
      <dl className="space-y-4 text-sm">
        <Detail label="種類" value={selected.kind} />
        <Detail label="名称" value={selected.title} />
        <Detail label="ノードID" value={selected.id} />
        <Detail label="参照ID" value={selected.sourceId} />
        <Detail label="資料適用範囲" value={selected.projectScope ?? "UNVERIFIED"} />
        <Detail label="版数" value={selected.sourceVersion ?? "未設定"} />
        <Detail label="参照パス" value={selected.sourcePath ?? "未設定（検証用）"} />
        <Detail label="承認scope" value={selected.approvalScope?.trim() || "未確認（承認根拠未取得）"} />
        <div><dt className="text-xs text-slate-400">状態</dt><dd className={`mt-1 inline-block rounded border px-2 py-1 text-xs ${statusClasses[selected.status]}`}>{selected.status}</dd></div>
        <Detail label="説明" value={selected.description} />
        <div><dt className="text-xs text-slate-400">承認証跡（各工程は独立）</dt><dd className="mt-2 space-y-2">{approvalFields.map(([label, key]) => <div key={key}><span className="text-xs text-slate-400">{label}：</span><span className="break-words">{evidenceText(selected.approvalEvidence?.[key])}</span></div>)}</dd></div>
      </dl>
      {cut ? <section className="mt-6 border-t border-white/10 pt-4" aria-label="CUT詳細">
        <h3 className="mb-3 text-sm font-semibold">CUT詳細（検証用）</h3>
        <dl className="space-y-3 text-sm">
          <Detail label="SCENE" value={cut.sceneId} />
          <Detail label="SCRIPT" value={cut.scriptId} />
          <Detail label="目的" value={cut.purpose} />
          <Detail label="人物動作" value={cut.action} />
          <Detail label="カメラ" value={cut.camera} />
          <Detail label="音響" value={cut.sound} />
          <Detail label="連続性" value={cut.continuity} />
          <Detail label="前CUT参照ID" value={cut.previousCutId?.trim() || "UNVERIFIED（未指定）"} />
          <Detail label="CUT順序の根拠ID" value={cut.sequenceEvidenceId?.trim() ? `${cut.sequenceEvidenceId.trim()}（参照先未検証）` : "UNVERIFIED（未指定）"} />
          <Detail label="CUT順序の循環検査" value={cycleDetected ? "MISMATCH（前CUT参照に循環あり・比較停止）" : "循環未検出（順序の正当性は未検証）"} />
          <Detail label="CUT開始状態" value={boundaryText(cut.startState)} />
          <Detail label="CUT終了状態" value={boundaryText(cut.endState)} />
          <Detail label="前CUTとの自動比較（明示された前CUT参照のみ）" value={continuityCheck ? `${continuityCheck.status} · ${continuityCheck.reasons.join(" / ") || "5項目の文字列一致（根拠IDの実在性・映像QCは未検証）"}` : "UNVERIFIED（前CUT参照・順序根拠・資料適用範囲のいずれかが未確認）"} />
          <Detail label="尺" value={cut.timing} />
          <div><dt className="text-xs text-slate-400">QC</dt><dd className={`mt-1 inline-block rounded border px-2 py-1 text-xs ${statusClasses[cut.qc]}`}>{cut.qc}</dd></div>
        </dl>
      </section> : null}
      <h3 className="mt-6 border-t border-white/10 pt-4 text-sm font-semibold">関連ノード</h3>
      {related.length > 0 ? <ul className="mt-3 space-y-2">
        {related.map((edge) => {
          const otherId = edge.source === selected.id ? edge.target : edge.source;
          const other = nodes.find((node) => node.id === otherId);
          return <li key={edge.id}><button type="button" className="w-full rounded-lg border border-white/10 p-2 text-left text-xs hover:border-cyan-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300" onClick={() => onSelect(otherId)}>{edge.label} · {other?.title ?? "参照不明"}</button></li>;
        })}
      </ul> : <p className="mt-3 text-sm text-slate-400">関連ノードはありません。</p>}
    </aside>
  );
}

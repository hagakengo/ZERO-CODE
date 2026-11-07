"use client";

import { useState } from "react";

type Status = "DRAFT" | "APPROVED" | "HOLD" | "NOT_FOUND" | "UNVERIFIED";
type Kind = "SCRIPT" | "SCENE" | "CUT" | "CHARACTER" | "ASSET";
type ProductionNode = {
  id: string;
  kind: Kind;
  title: string;
  status: Status;
  sourceId: string;
  sourceVersion?: string;
  sourcePath?: string;
  approvalScope?: string;
  description: string;
};
type Connection = { source: string; target: string; label: string };

// TEST DATA ONLY: no canonical production records, backend endpoints, or external services.
const sampleNodes: readonly ProductionNode[] = [
  { id: "test-script-01", kind: "SCRIPT", title: "検証用脚本", status: "DRAFT", sourceId: "TEST-SCRIPT-001", sourceVersion: "test-r01", description: "架空の脚本ノード。実際の正史や承認記録ではありません。" },
  { id: "test-scene-01", kind: "SCENE", title: "検証用シーン", status: "UNVERIFIED", sourceId: "TEST-SCENE-001", description: "構成と参照関係の表示確認にのみ使用します。" },
  { id: "test-cut-01", kind: "CUT", title: "検証用CUT 01", status: "HOLD", sourceId: "TEST-CUT-001", description: "制作保留状態の表示確認用。" },
  { id: "test-cut-02", kind: "CUT", title: "検証用CUT 02", status: "NOT_FOUND", sourceId: "TEST-CUT-002", description: "参照素材が未確認であることの表示確認用。未制作を意味しません。" },
  { id: "test-character-01", kind: "CHARACTER", title: "検証用キャラクター", status: "DRAFT", sourceId: "TEST-CHAR-001", sourceVersion: "test-r01", description: "実在のキャラクター設定・MASTERではありません。" },
  { id: "test-asset-01", kind: "ASSET", title: "検証用素材", status: "UNVERIFIED", sourceId: "TEST-ASSET-001", description: "実ファイルを読み込まない参照表示テストです。" },
];
const sampleConnections: readonly Connection[] = [
  { source: "test-script-01", target: "test-scene-01", label: "CONTAINS" },
  { source: "test-scene-01", target: "test-cut-01", label: "CONTAINS" },
  { source: "test-scene-01", target: "test-cut-02", label: "CONTAINS" },
  { source: "test-character-01", target: "test-cut-01", label: "APPEARS_IN" },
  { source: "test-asset-01", target: "test-cut-02", label: "REFERENCES" },
];
const kindLabels: Record<Kind, string> = {
  SCRIPT: "脚本", SCENE: "シーン", CUT: "カット", CHARACTER: "キャラクター", ASSET: "素材",
};
const statusClasses: Record<Status, string> = {
  DRAFT: "border-amber-400/40 text-amber-200",
  APPROVED: "border-emerald-400/40 text-emerald-200",
  HOLD: "border-orange-400/40 text-orange-200",
  NOT_FOUND: "border-rose-400/40 text-rose-200",
  UNVERIFIED: "border-slate-400/40 text-slate-200",
};

export default function ProductionCanvasPage() {
  const [selectedId, setSelectedId] = useState<string>(sampleNodes[0].id);
  const selected = sampleNodes.find((node) => node.id === selectedId) ?? sampleNodes[0];
  const related = sampleConnections.filter((edge) => edge.source === selected.id || edge.target === selected.id);
  return (
    <main className="min-h-screen bg-[#090b0f] px-4 py-8 text-slate-100 md:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-6 flex flex-wrap items-start justify-between gap-4 border-b border-white/10 pb-5">
          <div>
            <a className="text-sm text-cyan-300 underline underline-offset-4" href="/">← Dashboard</a>
            <h1 className="mt-3 text-2xl font-semibold">制作キャンバス / MVP</h1>
            <p className="mt-2 text-sm text-slate-400">脚本・シーン・CUT・人物・素材の参照関係を確認するための試作画面</p>
          </div>
          <span className="rounded-lg border border-cyan-400/40 px-3 py-2 text-xs font-semibold text-cyan-200">READ ONLY · TEST DATA</span>
        </header>
        <p role="note" className="mb-5 rounded-xl border border-amber-400/30 bg-amber-500/10 p-4 text-sm text-amber-100">
          ここに表示されるID・状態・資料はすべて架空の検証用データです。ZERO CODEの正史、MASTER、承認記録、実在素材には接続していません。
        </p>
        <div className="grid gap-4 lg:grid-cols-[210px_minmax(0,1fr)_310px]">
          <nav aria-label="検証用ノード一覧" className="rounded-xl border border-white/10 bg-[#10151c] p-4">
            <h2 className="mb-3 text-sm font-semibold">構成ツリー</h2>
            <div className="space-y-2">
              {sampleNodes.map((node) => (
                <button key={node.id} type="button" onClick={() => setSelectedId(node.id)}
                  aria-current={selected.id === node.id ? "true" : undefined}
                  className={`w-full rounded-lg border p-3 text-left text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300 ${selected.id === node.id ? "border-cyan-400 bg-cyan-400/10" : "border-white/10 hover:border-white/30"}`}>
                  <span className="block text-xs text-slate-400">{kindLabels[node.kind]}</span>
                  <span className="mt-1 block font-medium">{node.title}</span>
                </button>
              ))}
            </div>
          </nav>
          <section aria-label="検証用関係キャンバス" className="min-h-[440px] rounded-xl border border-white/10 bg-[#10151c] p-4">
            <div className="mb-4 flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold">参照グラフ</h2>
              <span className="text-xs text-slate-400">ノードを選択して詳細を表示</span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {sampleNodes.map((node) => (
                <button type="button" key={node.id} onClick={() => setSelectedId(node.id)}
                  aria-pressed={selected.id === node.id}
                  className={`rounded-xl border p-4 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300 ${selected.id === node.id ? "border-cyan-400 bg-cyan-400/10" : "border-white/15 bg-[#0b1018] hover:border-white/40"}`}>
                  <span className="text-xs tracking-wider text-cyan-300">{node.kind}</span>
                  <span className="mt-2 block font-medium">{node.title}</span>
                  <span className={`mt-3 inline-block rounded border px-2 py-1 text-xs ${statusClasses[node.status]}`}>{node.status}</span>
                </button>
              ))}
            </div>
            <div className="mt-6 border-t border-white/10 pt-4">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">参照関係（検証用）</h3>
              <ul className="space-y-2">
                {sampleConnections.map((edge) => (
                  <li key={`${edge.source}-${edge.target}`} className="rounded-lg bg-white/5 px-3 py-2 text-xs text-slate-300">
                    {sampleNodes.find((node) => node.id === edge.source)?.sourceId ?? "参照不明"} → {sampleNodes.find((node) => node.id === edge.target)?.sourceId ?? "参照不明"} <span className="text-cyan-300">({edge.label})</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>
          <aside aria-live="polite" aria-label="選択ノードの詳細" className="rounded-xl border border-white/10 bg-[#10151c] p-4">
            <h2 className="mb-4 text-sm font-semibold">ノード詳細</h2>
            <dl className="space-y-4 text-sm">
              {([
                ["種類", selected.kind],
                ["名称", selected.title],
                ["ノードID", selected.id],
                ["参照ID", selected.sourceId],
                ["版数", selected.sourceVersion ?? "未設定"],
                ["参照パス", selected.sourcePath ?? "未設定（検証用）"],
                ["承認scope", selected.approvalScope ?? "未確認（承認なし）"],
              ] as const).map(([label, value]) => (
                <div key={label}>
                  <dt className="text-xs text-slate-400">{label}</dt>
                  <dd className="mt-1 break-all">{value}</dd>
                </div>
              ))}
              <div><dt className="text-xs text-slate-400">状態</dt><dd className={`mt-1 inline-block rounded border px-2 py-1 text-xs ${statusClasses[selected.status]}`}>{selected.status}</dd></div>
              <div><dt className="text-xs text-slate-400">説明</dt><dd className="mt-1 leading-relaxed">{selected.description}</dd></div>
            </dl>
            <h3 className="mt-6 border-t border-white/10 pt-4 text-sm font-semibold">関連ノード</h3>
            {related.length ? (
              <ul className="mt-3 space-y-2">
                {related.map((edge) => {
                  const otherId = edge.source === selected.id ? edge.target : edge.source;
                  const other = sampleNodes.find((node) => node.id === otherId);
                  return <li key={`${edge.source}-${edge.target}`}>
                    <button type="button" className="w-full rounded-lg border border-white/10 p-2 text-left text-xs hover:border-cyan-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300"
                      onClick={() => setSelectedId(otherId)}>{edge.label} · {other?.title ?? "参照不明"}</button>
                  </li>;
                })}
              </ul>
            ) : <p className="mt-3 text-sm text-slate-400">関連ノードはありません。</p>}
          </aside>
        </div>
        <footer className="mt-5 text-xs text-slate-500">ZCS-WORK-CANVAS-002 r02 · DRAFT implementation · No API / DB / video generation / approval writes</footer>
      </div>
    </main>
  );
}

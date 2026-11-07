import { ProductionCanvas } from "./ProductionCanvas";

export default function ProductionCanvasPage() {
  return (
    <main className="min-h-screen bg-[#090b0f] px-4 py-8 text-slate-100 md:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-6 flex flex-wrap items-start justify-between gap-4 border-b border-white/10 pb-5">
          <div>
            <a className="text-sm text-cyan-300 underline underline-offset-4" href="/">← Dashboard</a>
            <h1 className="mt-3 text-2xl font-semibold">制作キャンバス / MVP v2</h1>
            <p className="mt-2 text-sm text-slate-400">脚本・シーン・CUT・人物・素材を移動・拡大して参照関係を確認する試作画面</p>
          </div>
          <span className="rounded-lg border border-cyan-400/40 px-3 py-2 text-xs font-semibold text-cyan-200">READ ONLY · TEST DATA</span>
        </header>
        <p role="note" className="mb-5 rounded-xl border border-amber-400/30 bg-amber-500/10 p-4 text-sm text-amber-100">
          ここに表示されるID・状態・資料はすべて架空の検証用データです。位置変更は保存されず、ZERO CODEの正史、MASTER、承認記録、実在素材には接続していません。
        </p>
        <ProductionCanvas />
        <footer className="mt-5 text-xs text-slate-500">ZCS-WORK-CANVAS-006 r01 · DRAFT implementation · No API / DB / video generation / approval writes</footer>
      </div>
    </main>
  );
}

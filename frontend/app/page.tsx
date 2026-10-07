"use client";
import { useEffect, useState } from "react";

type Mission = { code: string; title: string; status: string; progress: number };
type Status = { day: number; level: number; youtube: { subscribers: number; views: number }; tiktok: { followers: number; views: number }; total_revenue_yen: number; mission: Mission };
export default function Dashboard() {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState(false);
  const online = status !== null;
  const missions = status ? [status.mission] : [];
  useEffect(() => {
    const controller = new AbortController();
    // Accept the original /api/missions env value as well as an API origin.
    const base = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "").replace(/\/api\/(missions|status)$/, "");
    fetch(`${base}/api/status`, { signal: controller.signal, cache: "no-store" })
      .then(r => { if (!r.ok) throw new Error("Status unavailable"); return r.json(); })
      .then(setStatus)
      .catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => controller.abort();
  }, []);
  return <main className="min-h-screen bg-[#090b0f] px-6 py-10 md:px-16">
    <header className="mx-auto flex max-w-6xl items-center justify-between border-b border-white/10 pb-6"><div><p className="text-xs tracking-[0.35em] text-cyan-300">ZERO CODE OS / 0.1</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">Dashboard</h1></div><span role="status" className={`rounded-full border px-3 py-1 text-xs ${online ? "border-cyan-400/40 text-cyan-300" : "border-white/20 text-white/50"}`}>{online ? "SYSTEM ONLINE" : error ? "UNAVAILABLE" : "CONNECTING"}</span></header>
    {error && <p role="alert" className="mx-auto mt-8 max-w-6xl text-white/70">データを取得できませんでした。APIの起動を確認してページを再読み込みしてください。</p>}
    {status && <section aria-label="System metrics" className="mx-auto mt-8 max-w-6xl font-mono">
      <div className="mb-6 flex gap-8 text-cyan-200"><p>DAY <span>{status.day}</span></p><p>LEVEL <span>{status.level}</span></p></div>
      <div className="grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border border-cyan-300/20 bg-[#10151c]/80 p-6"><h2 className="mb-6 text-cyan-300">YouTube</h2><dl className="space-y-4"><div className="flex justify-between gap-4"><dt>Subscribers</dt><dd>{status.youtube.subscribers}</dd></div><div className="flex justify-between gap-4"><dt>Views</dt><dd>{status.youtube.views}</dd></div></dl></article>
        <article className="rounded-xl border border-cyan-300/20 bg-[#10151c]/80 p-6"><h2 className="mb-6 text-cyan-300">TikTok</h2><dl className="space-y-4"><div className="flex justify-between gap-4"><dt>Followers</dt><dd>{status.tiktok.followers}</dd></div><div className="flex justify-between gap-4"><dt>Views</dt><dd>{status.tiktok.views}</dd></div></dl></article>
        <article className="rounded-xl border border-cyan-300/20 bg-[#10151c]/80 p-6"><h2 className="text-cyan-300">TOTAL REVENUE</h2><p className="mt-6 break-all text-4xl">¥{status.total_revenue_yen}</p></article>
      </div>
    </section>}
    <section className="mx-auto mt-10 max-w-6xl"><p className="text-sm uppercase tracking-[0.25em] text-white/40">Current mission</p>{missions.map(m => <article key={m.code} className="mt-4 rounded-2xl border border-cyan-300/20 bg-[#10151c] p-8 shadow-2xl shadow-cyan-950/20"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="font-mono text-sm text-cyan-300">{m.code}</p><h2 className="mt-3 text-2xl font-medium">{m.title}</h2></div><span className="rounded-full bg-cyan-300/10 px-3 py-1 text-xs text-cyan-200">{m.status}</span></div><div className="mt-10"><div className="flex justify-between text-xs text-white/45"><span>Progress</span><span>{m.progress}%</span></div><div className="mt-2 h-2 rounded-full bg-white/10"><div className="h-2 rounded-full bg-cyan-300" style={{width: `${m.progress}%`}} /></div></div></article>)}</section>
  </main>;
}

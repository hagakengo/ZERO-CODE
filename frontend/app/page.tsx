"use client";
import { useEffect, useState } from "react";

type Mission = { code: string; title: string; status: string; progress: number };
export default function Dashboard() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [online, setOnline] = useState(false);
  useEffect(() => { fetch(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/missions").then(r => r.json()).then(setMissions).then(() => setOnline(true)).catch(() => setOnline(false)); }, []);
  return <main className="min-h-screen bg-[#090b0f] px-6 py-10 md:px-16">
    <header className="mx-auto flex max-w-6xl items-center justify-between border-b border-white/10 pb-6"><div><p className="text-xs tracking-[0.35em] text-cyan-300">ZERO CODE OS / 0.1</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">Dashboard</h1></div><span className={`rounded-full border px-3 py-1 text-xs ${online ? "border-emerald-400/40 text-emerald-300" : "border-white/20 text-white/50"}`}>{online ? "SYSTEM ONLINE" : "CONNECTING"}</span></header>
    <section className="mx-auto mt-10 max-w-6xl"><p className="text-sm uppercase tracking-[0.25em] text-white/40">Current mission</p>{missions.map(m => <article key={m.code} className="mt-4 rounded-2xl border border-cyan-300/20 bg-[#10151c] p-8 shadow-2xl shadow-cyan-950/20"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="font-mono text-sm text-cyan-300">{m.code}</p><h2 className="mt-3 text-2xl font-medium">{m.title}</h2></div><span className="rounded-full bg-cyan-300/10 px-3 py-1 text-xs text-cyan-200">{m.status}</span></div><div className="mt-10"><div className="flex justify-between text-xs text-white/45"><span>Progress</span><span>{m.progress}%</span></div><div className="mt-2 h-2 rounded-full bg-white/10"><div className="h-2 rounded-full bg-cyan-300" style={{width: `${m.progress}%`}} /></div></div></article>)}</section>
  </main>;
}

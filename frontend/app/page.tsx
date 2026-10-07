"use client";
import { FormEvent, useEffect, useRef, useState } from "react";

type Mission = { code: string; title: string; status: string; progress: number | null; target_value: number; current_value: number | null };
type Counters = { youtube: { subscribers: number; views: number }; tiktok: { followers: number; views: number }; total_revenue_yen: number };
type Status = Counters & {
  day: number; level: number; date: string; today: string; timezone: string; mission: Mission;
  observed_on: Record<string, string | null>;
  delta: { youtube: { subscribers: number | null; views: number | null }; tiktok: { followers: number | null; views: number | null }; total_revenue_yen: number | null };
};
type HistoryRow = { date: string; computed_day: number; observed_on: Record<string, string | null>; delta: Record<string, number | null> } & Record<"youtube_subscribers" | "youtube_views" | "tiktok_followers" | "tiktok_views" | "total_revenue_yen", number>;
type Progression = { day: number; level: number; calculated_level: number; legacy_level: number; start_on: string | null; missions: Mission[]; history_summary: { record_count: number; first_date: string; last_date: string }; level_rules: { level: number; requirements: Record<string, number> }[] };
const historyFields = ["youtube_subscribers", "youtube_views", "tiktok_followers", "tiktok_views", "total_revenue_yen"] as const;
type Integration = { state: "disconnected" | "connected" | "error"; configured: boolean; error: string | null; warning: string | null; last_synced_at: string | null; last_observed_on: string | null };
const base = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "").replace(/\/api\/(missions|status)$/, "");
const fields = [
  { key: "tiktok_followers", label: "TikTok followers" },
  { key: "tiktok_views", label: "TikTok views" },
  { key: "total_revenue_yen", label: "Total revenue (JPY)" },
] as const;
type ManualField = typeof fields[number]["key"];
const emptyForm = { tiktok_followers: "", tiktok_views: "", total_revenue_yen: "" };
const panel = "rounded-xl border border-cyan-300/20 bg-[#10151c]/80 p-6";
function Delta({ value, yen = false }: { value: number | null; yen?: boolean }) {
  return <span className="block text-xs text-cyan-200/70">前日比 {value === null ? "—" : `${value >= 0 ? "+" : "−"}${yen ? "¥" : ""}${Math.abs(value).toLocaleString("ja-JP")}`}</span>;
}

export default function Dashboard() {
  const [history, setHistory] = useState<HistoryRow[]>([]);
  const [progression, setProgression] = useState<Progression | null>(null);
  const [historyError, setHistoryError] = useState("");
  async function refreshProgression(signal?: AbortSignal) {
    try {
      const responses = await Promise.all(["/api/metrics/history?limit=30", "/api/progression"].map(path => fetch(`${base}${path}`, { signal, cache: "no-store" })));
      if (responses.some(response => !response.ok)) throw new Error();
      const [rows, progress] = await Promise.all(responses.map(response => response.json()));
      setHistory(rows); setProgression(progress); setHistoryError("");
    } catch { if (!signal?.aborted) setHistoryError("履歴・進行を取得できません。表示がある場合は前回取得分です。"); }
  }
  const [status, setStatus] = useState<Status | null>(null);
  const [integration, setIntegration] = useState<Integration | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncError, setSyncError] = useState("");
  const [syncMessage, setSyncMessage] = useState("");
  const [error, setError] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const [saveError, setSaveError] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${base}/api/status`, { signal: controller.signal, cache: "no-store" })
      .then(r => { if (!r.ok) throw new Error("Status unavailable"); return r.json(); })
      .then(setStatus)
      .catch(() => { if (!controller.signal.aborted) setError(true); });
    fetch(`${base}/api/integrations/youtube/status`, { signal: controller.signal, cache: "no-store" })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); }).then(setIntegration)
      .catch(() => { if (!controller.signal.aborted) setSyncError("YouTube接続状態を取得できません。"); });
    void refreshProgression(controller.signal);
    return () => controller.abort();
  }, []);
  async function syncYouTube() {
    if (savingRef.current) return;
    savingRef.current = true; setSyncing(true); setSyncError(""); setSyncMessage("");
    try {
      const response = await fetch(`${base}/api/integrations/youtube/sync`, { method: "POST" });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "YouTube同期に失敗しました。");
      setStatus(result.status); setIntegration(result.integration); setError(false);
      setSyncMessage("YouTubeの実測値を保存しました。");
      await refreshProgression();
    } catch (error) {
      setSyncError(error instanceof Error ? error.message : "同期結果を確認できません。");
      try {
        const response = await fetch(`${base}/api/integrations/youtube/status`, { cache: "no-store" });
        if (response.ok) setIntegration(await response.json());
      } catch { /* Preserve the last known status when offline. */ }
    } finally { savingRef.current = false; setSyncing(false); }
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (savingRef.current) return;
    setSaveError(""); setMessage("");
    const payload: Partial<Record<ManualField, number>> = {};
    for (const { key } of fields) {
      const raw = form[key].trim();
      if (raw === "") continue;
      const value = Number(raw);
      if (!/^\d+$/.test(raw) || !Number.isSafeInteger(value)) {
        setSaveError("0以上の整数を入力してください。"); return;
      }
      payload[key] = value;
    }
    if (!Object.keys(payload).length) { setSaveError("更新する項目を1つ以上入力してください。"); return; }
    savingRef.current = true; setSaving(true);
    try {
      const response = await fetch(`${base}/api/metrics/manual`, {
        method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error("Update failed");
      const updated: Status = await response.json();
      setStatus(updated); setForm(emptyForm); setError(false);
      setMessage(`${updated.date} の記録を保存しました。`);
      await refreshProgression();
    } catch { setSaveError("保存結果を確認できませんでした。接続を確認して再保存してください（累計値なので重複加算されません）。"); }
    finally { savingRef.current = false; setSaving(false); }
  }
  function observed(key: string) {
    const day = status?.observed_on[key];
    return day ? `最終入力・取得 ${day}` : "未入力・未取得（初期値／既存値）";
  }
  const mission = status?.mission;
  return <main className="min-h-screen bg-[#090b0f] px-6 py-10 md:px-16">
    <header className="mx-auto flex max-w-6xl items-center justify-between gap-4 border-b border-white/10 pb-6">
      <div><p className="text-xs tracking-[0.35em] text-cyan-300">ZERO CODE OS / 0.4</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">Dashboard</h1></div>
      <span role="status" className={`rounded-full border px-3 py-1 text-xs ${status ? "border-cyan-400/40 text-cyan-300" : "border-white/20 text-white/50"}`}>{status ? "SYSTEM ONLINE" : error ? "UNAVAILABLE" : "CONNECTING"}</span>
    </header>
    {error && <p role="alert" className="mx-auto mt-8 max-w-6xl text-white/70">データを取得できませんでした。APIの起動を確認してページを再読み込みしてください。</p>}
    {status && <>
      <section aria-label="System metrics" className="mx-auto mt-8 max-w-6xl font-mono">
        <div className="mb-3 flex gap-8 text-cyan-200"><p>DAY {status.day}</p><p>LEVEL {status.level}</p></div>
        <p className="mb-6 text-xs leading-6 text-white/50">記録日 {status.date} / {status.timezone}{status.date !== status.today && " / 本日未更新"}<br />前日比は記録日の1日前との比較。両日の実測値がない場合は — 。</p>
        <div className="grid gap-4 md:grid-cols-3">
          <article className={panel}><h2 className="mb-2 text-cyan-300">YouTube</h2><p className="mb-5 text-xs text-white/50">{integration ? ({ disconnected: "未接続", connected: "接続済み", error: "エラー" }[integration.state]) : "接続状態を確認中"} / {observed("youtube")}</p>
            <dl className="space-y-4">{(["subscribers", "views"] as const).map(key => <div key={key} className="flex justify-between gap-4"><dt>{key === "subscribers" ? "Subscribers" : "Views"}</dt><dd className="text-right">{status.observed_on.youtube ? status.youtube[key].toLocaleString("ja-JP") : "未取得"}<Delta value={status.delta.youtube[key]} /></dd></div>)}</dl>
            <button type="button" disabled={syncing || saving} onClick={syncYouTube} className="mt-6 rounded border border-cyan-300/50 px-4 py-2 text-sm text-cyan-200 disabled:opacity-50">{syncing ? "SYNCING YOUTUBE…" : "SYNC YOUTUBE"}</button>
            <p className="mt-3 text-xs text-white/50">最終同期 {integration?.last_synced_at ? new Date(integration.last_synced_at + (integration.last_synced_at.endsWith("Z") ? "" : "Z")).toLocaleString("ja-JP") : "未取得"}</p>
            {integration && !integration.configured && <p className="mt-2 text-xs text-white/60">READMEのGoogle Cloud設定・OAuth認証を完了してください。</p>}
            {(syncError || integration?.error) && <p role="alert" className="mt-3 text-xs text-red-200">{syncError || integration?.error}</p>}
            {integration?.warning && <p className="mt-3 text-xs text-amber-200">{integration.warning}</p>}
            <p role="status" className="mt-2 text-xs text-cyan-200">{syncMessage}</p>
          </article>
          <article className={panel}><h2 className="mb-6 text-cyan-300">TikTok</h2><dl className="space-y-5">{(["followers", "views"] as const).map(key => <div key={key}><div className="flex justify-between gap-4"><dt>{key === "followers" ? "Followers" : "Views"}</dt><dd className="text-right">{status.tiktok[key].toLocaleString("ja-JP")}<Delta value={status.delta.tiktok[key]} /></dd></div><p className="mt-1 text-xs text-white/50">{observed(`tiktok_${key}`)}</p></div>)}</dl></article>
          <article className={panel}><h2 className="text-cyan-300">TOTAL REVENUE</h2><p className="mt-6 break-all text-4xl">¥{status.total_revenue_yen.toLocaleString("ja-JP")}</p><div className="mt-3"><Delta value={status.delta.total_revenue_yen} yen /></div><p className="mt-3 text-xs text-white/50">{observed("total_revenue_yen")}</p></article>
        </div>
      </section>
      {mission && <section className="mx-auto mt-10 max-w-6xl"><p className="text-sm uppercase tracking-[0.25em] text-white/40">Current mission</p><article className={`${panel} mt-4 shadow-2xl shadow-cyan-950/20`}><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="font-mono text-sm text-cyan-300">{mission.code}</p><h2 className="mt-3 text-2xl font-medium">{mission.title}</h2></div><span className="rounded-full bg-cyan-300/10 px-3 py-1 text-xs text-cyan-200">{mission.status}</span></div><div className="mt-8"><div className="flex justify-between text-xs text-white/60"><span>Progress / {mission.current_value ?? "—"} / {mission.target_value}</span><span>{mission.progress === null ? "—" : `${Number(mission.progress.toFixed(2))}%`}</span></div><div role="progressbar" aria-label="Mission progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={mission.progress ?? undefined} className="mt-2 h-2 rounded-full bg-white/10"><div className="h-2 rounded-full bg-cyan-300" style={{ width: `${mission.progress ?? 0}%` }} /></div></div></article></section>}
      <section aria-label="Progression" className={`${panel} mx-auto mt-10 max-w-6xl`}>
        <h2 className="font-mono tracking-widest text-cyan-300">PROGRESSION</h2>
        {historyError && <p role="alert" className="mt-3 text-amber-200">{historyError}</p>}
        {progression && <><p className="mt-4 font-mono text-xl">DAY {progression.day} / LEVEL {progression.level}</p>
          <p className="mt-2 text-xs text-white/50">開始日 {progression.start_on ?? "最初の実測待ち"} / 暦日で進行 / ルールLEVEL {progression.calculated_level} / 既存LEVEL {progression.legacy_level}</p>
          <p className="mt-3 text-sm text-white/60">履歴 {progression.history_summary.record_count}件 / {progression.history_summary.first_date} → {progression.history_summary.last_date}</p>
          <div className="mt-4 space-y-2 text-xs text-white/50">{progression.level_rules.map(rule => <p key={rule.level}>LEVEL {rule.level}: {Object.entries(rule.requirements).map(([key, value]) => `${key} ≥ ${value.toLocaleString("ja-JP")}`).join(" / ")}（全条件・実測必須）</p>)}</div>
          <div className="mt-6 grid gap-3 md:grid-cols-2">{progression.missions.map(item => <article key={item.code} className="rounded border border-cyan-300/20 p-4"><p className="font-mono text-cyan-200">{item.code} / {item.status.toUpperCase()}</p><p className="mt-2">{item.title}</p><p className="mt-3 text-xs text-white/60">{item.current_value ?? "—"} / {item.target_value} · {item.progress === null ? "未取得" : `${Number(item.progress.toFixed(2))}%`}</p></article>)}</div>
          <p className="mt-4 text-xs text-white/40">ACHIEVEMENTS / 未実装</p></>}
      </section>
      <section aria-label="History" className={`${panel} mx-auto mt-10 max-w-6xl`}>
        <h2 className="font-mono tracking-widest text-cyan-300">HISTORY</h2>
        <p className="mt-3 text-xs text-white/50">最新30記録。Δは前暦日比。持ち越し値は最終実測日を表示し、未測定は未取得。欠損日は補完しません。</p>
        <div className="mt-5 overflow-x-auto"><table className="w-full whitespace-nowrap text-left text-xs"><thead><tr className="border-b border-white/10 text-cyan-200"><th className="p-3">DATE / DAY</th>{historyFields.map(field => <th key={field} className="p-3">{field}</th>)}</tr></thead>
          <tbody>{history.map(row => <tr key={row.date} className="border-b border-white/10"><th className="p-3 font-mono">{row.date} / {row.computed_day}</th>{historyFields.map(field => {
            const observation = row.observed_on[field.startsWith("youtube_") ? "youtube" : field];
            const delta = row.delta[field];
            return <td key={field} className="p-3 font-mono">{observation ? `${field === "total_revenue_yen" ? "¥" : ""}${row[field].toLocaleString("ja-JP")}` : "未取得"}<span className="mt-1 block text-cyan-200/60">Δ {delta === null ? "—" : `${delta >= 0 ? "+" : ""}${delta.toLocaleString("ja-JP")}`}</span><span className="block text-white/40">{observation ?? "実測なし"}</span></td>;
          })}</tr>)}</tbody></table></div>
      </section>
      <section className="mx-auto mt-10 max-w-6xl"><form onSubmit={save} className={panel}>
        <h2 className="font-mono text-cyan-300">UPDATE MANUAL</h2>
        <p className="mt-3 text-sm leading-6 text-white/60">今日の累計値を入力してください（{status.timezone}）。空欄は変更せず、0は実測ゼロとして保存します。同日の再保存は上書き、翌日は新しい履歴になります。</p>
        <fieldset disabled={saving || syncing} className="mt-6 grid gap-5 md:grid-cols-3">{fields.map(({ key, label }) => <label key={key} className="text-sm text-white/80">{label}<input name={key} type="number" min="0" max="9007199254740991" step="1" inputMode="numeric" placeholder="変更しない" value={form[key]} onChange={event => setForm({ ...form, [key]: event.target.value })} className="mt-2 w-full rounded border border-cyan-300/25 bg-black/30 px-3 py-3 font-mono text-cyan-100 outline-none focus:border-cyan-300 disabled:opacity-50" /></label>)}</fieldset>
        <button disabled={saving || syncing} type="submit" className="mt-6 rounded border border-cyan-300/50 bg-cyan-300/10 px-6 py-3 font-mono text-sm text-cyan-200 hover:bg-cyan-300/20 disabled:opacity-50">{saving ? "SAVING…" : "SAVE TODAY"}</button>
        {saveError && <p role="alert" className="mt-4 text-sm text-white/80">{saveError}</p>}
        <p role="status" className="mt-4 text-sm text-cyan-200">{message}</p>
      </form></section>
    </>}
  </main>;
}

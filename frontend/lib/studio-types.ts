export type Media = { media_id: string; sha256: string; bytes: number; format: string; storage: string };
export type Drawing = { id: string; title: string; media: Media | null };
export type Version = { version: string; state: string; verdict: string; drawings: Drawing[]; video: Media | null; documents: { title: string; media: Media }[] };
export type Cut = { id: string; episode: string; title: string; purpose: string; stage: string; verdict: string; latest: string | null; next_stage_allowed: boolean; producer_approval: string; versions: Version[] };
export type Asset = { id: string; title: string; project: string; version: string; state: string; approval: string; source: string; review: string; media: Media | null; availability: string };
export type Review = { id: string; version: string; verdict: string; scope: string; video_scope: string; date: string | null; actor: string; reason: string; keys: Record<string,string>; next_actions: string[] };
export type StudioData = { revision: number; source_sha256: string; imported_at: string; mode: string; projects: {id: string; title: string; state: string}[]; assets: Asset[]; history: {date: string | null; note: string}[]; cuts: Cut[]; reviews: Review[] };
export const mediaURL = (m: Media) => `/api/studio/media/${m.media_id}`;

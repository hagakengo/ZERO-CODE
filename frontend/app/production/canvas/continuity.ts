import type { CutBoundaryState } from "./types";

export type ContinuityResult =
  | { status: "UNVERIFIED"; reasons: string[] }
  | { status: "MATCH"; reasons: string[] }
  | { status: "MISMATCH"; reasons: string[] };

const fields = ["characterPosition", "pose", "facing", "props", "camera"] as const;
const labels: Record<(typeof fields)[number], string> = {
  characterPosition: "人物位置",
  pose: "姿勢",
  facing: "向き",
  props: "小道具",
  camera: "カメラ",
};

// Read-only comparison. An absent field is unknown, never a match or mismatch.
// A difference is flagged for human review; intentional cuts may legitimately differ.
export function compareCutBoundaries(
  previousEnd?: CutBoundaryState,
  nextStart?: CutBoundaryState,
): ContinuityResult {
  if (!previousEnd || !nextStart) {
    return { status: "UNVERIFIED", reasons: ["前CUT終了状態または次CUT開始状態が未記録"] };
  }

  const missing: string[] = [];
  const mismatches: string[] = [];
  for (const field of fields) {
    const before = previousEnd[field]?.trim();
    const after = nextStart[field]?.trim();
    if (!before || !after) {
      missing.push(`${labels[field]}: 比較根拠不足`);
    } else if (before !== after) {
      mismatches.push(`${labels[field]}: 前「${before}」→ 次「${after}」`);
    }
  }
  if (!previousEnd.evidenceId?.trim() || !nextStart.evidenceId?.trim()) {
    missing.push("前後CUT境界状態の根拠IDが未記録");
  }
  if (mismatches.length) return { status: "MISMATCH", reasons: [...mismatches, ...missing] };
  if (missing.length) return { status: "UNVERIFIED", reasons: missing };
  return { status: "MATCH", reasons: [] };
}

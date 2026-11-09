# ZCS-DIRECTOR-CANVAS-TEST-056 v0.1｜CUT連続性テスト設計と検証記録

- ID: ZCS-DIRECTOR-CANVAS-TEST-056
- Version: v0.1
- State: DRAFT
- Date: 2026-11-09
- PR: https://github.com/hagakengo/ZERO-CODE/pull/24
- Scope: 検証用Canvas。正史、MASTER、映像素材は変更しない。

## 取得済み検証証拠

- Commit 9ba53d099c76e4cff2ce12853393f929128a5cc6: GitHub Actions CI #116 / run 42632905121 / completed success。
- 追加変更: frontend/tests/production-canvas.test.cjs に TypeScript transpileModule + VM 実行の関数テストを追加。対象関数 frontend/app/production/canvas/continuity.ts。
- ケース: 5項目一致=MATCH、向き不一致=MISMATCH、前CUT未記録=UNVERIFIED、部分一致=UNVERIFIED、姿勢不一致=MISMATCH。
- Commit 2d6e6dbfca15ce8f8df9868a547f56ed27af24f3: CI run 42634354115 completed success（frontend/backend/dependency-audit）。根拠ID欠落テストを含む。
- 最新の「不一致かつ根拠ID欠落」ケース追加後のCIは別途確認すること。未実行のテストをPASS扱いしない。

## 既知の制約

- 文字列完全一致による検証であり、同義語、人物の動き、意図的なカメラ変更、演技・物理連続性は自動評価しない。
- 配列順によるCUT前後関係の推測は廃止。明示的な previousCutId / sequenceEvidenceId、同一作品scope・SCENE・SCRIPTが必要。
- 根拠IDの文字列が存在しても、その参照先の実在性・正当性までは検証していない。
- MISMATCHはレビュー対象の差分検出であり、演出ミスの確定ではない。
- 動画の視聴、実ブラウザ操作、正式な承認証跡との突合は未実施。
- 本番への反映、PRマージ、正史・MASTER変更は別途プロデューサー承認を要する。

## 次工程

- 新HEADのCIジョブ内訳を確認。
- 実ブラウザで検証用CUT選択、未記録表示、スマートフォン幅、ノード操作を検証。
- 正式なCUT順序を導入する場合は出典とscopeを必須とする。

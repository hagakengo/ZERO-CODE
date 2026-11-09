# ZCS-DIRECTOR-CANVAS-GATES-053 v0.1｜監督統合監査・実装指示 DRAFT

> Source: Dropbox Paper doc id:yqPbZD8BxvAAAAAAAAAAjg, revision 1
> GitHub copy: DRAFT, read-only record; no canon/MASTER approval or production deployment.

Document ID: ZCS-DIRECTOR-CANVAS-GATES-053
Version: v0.1
Status: DRAFT / 監督中間レビュー
Date: 2026-11-09
Authority: 監督による実装・検証指示。正史・MASTER・公開・本番変更の承認ではない。
Storage: Dropbox Paper（本書）。OS・Obsidianへの同期は未確認。

## 1. 検証済み事実と出典
- GitHub `hagakengo/ZERO-CODE` PR #20 Canvas本体、PR #22 CI、PR #23 Next/PostCSS更新はDraft・未マージ。PR #23 HEAD `4c95a6a4357335942acc94afd8bfd407e60879e5` のCI成功を確認。ただし統合後の成功は未検証。
- PR #23 HEAD `frontend/app/production/canvas/types.ts` は単一の `status` と `approvalScope`、CUTの自由記述 `continuity` と単一 `qc` を持つ。脚本内容・統合ファイル・MASTER・映像QCの承認を独立管理する型はない。
- 同 `NodeDetails.tsx` は承認scope欠落時に「未確認（承認なし）」と表示する。未取得と未承認を混同するおそれがある。
- 同 `ProductionCanvas.tsx` はドラッグ座標を制限せず、接続線SVGは720×620固定。RESETは初期位置・パン・倍率に戻す実装。ブラウザ実機検証は未実施。
- `PROJECT_CONTEXT.md` と `ZERO_CODE_RULES.md` に旧『¥0から始まるAI副業』・匿名フード主人公・D1の記述がある。`docs/production/ZCS-VISUAL-001_v1.0.md` は現行SFアニメと旧企画の混同を明示的に禁止。`docs/production/LEGACY_CANON_CONFLICTS_PRELIMINARY.md` は2026-10-22時点の衝突点を記録。
- Dropboxの内部EP00『正しい世界』v08と内部EP01『分岐』r07を閲覧。メタデータ上のAPPROVEDと本文冒頭の限定的な承認・レビュー表現が一致しない箇所がある。承認対象を確定せずMASTERへ昇格しない。
- Dropbox `/ZeroCode/reference_assets/confirmed-ren-20261021.png`、`confirmed-yuna-20261021.png`、`/ZeroCode/production_assets/ZCS-WORK-ANIM-006/CUT-04/CUT-04_ren-character-reference_DRAFT.png` のファイル実在・メタデータを確認。画像内容・SHA-256・正式MASTER照合は未実施。
- 参照: [PR #20](https://github.com/hagakengo/ZERO-CODE/pull/20)、[PR #22](https://github.com/hagakengo/ZERO-CODE/pull/22)、[PR #23](https://github.com/hagakengo/ZERO-CODE/pull/23)、[映像品質基準](https://github.com/hagakengo/ZERO-CODE/blob/main/docs/production/ZCS-VISUAL-001_v1.0.md)。

## 2. 優先実装ゲート
1. **資料適用範囲**：`projectScope` は `CURRENT_ANIME | LEGACY_YEN_ZERO | OS | UNVERIFIED`。旧資料の現行正史への自動適用を禁止。現行作品の承認済み設定を変更しない。
2. **承認分離**：`scriptContent`、`integratedFile`、`masterAdoption`、`videoQc` の各状態と根拠IDを独立保持。あるAPPROVEDが他へ伝播しない。承認情報未取得と未承認を区別。
3. **CUT連続性**：CUTのstartState/endStateで人物・負傷・小道具・方向・時刻を追跡。脚本のみの照合で動画QCをPASSにしない。
4. **操作安全性**：ドラッグ座標制限、接続線追従、ズーム補正、RESET、キーボード・タッチ操作を検証。
5. **保存と監査**：元資料ID、版、出典パス、承認scope、証拠ID、取得日時、未確認事項を保持。自動同期・正本書換えは別途設計。

## 3. 受入条件
- A01：scope未取得は「未確認」と表示し、「承認なし」と断定しない。
- A02：脚本APPROVEDでもMASTER採用はUNVERIFIEDのまま。
- A03：統合ファイルREVIEWEDは正式承認と表示しない。
- A04：旧D1/匿名フード主人公を現行アニメに自動適用しない。
- A05：正式参照画像とDRAFT画像を混同しない。
- A06：既存Canvas検証ノード6件と既存テスト4件を維持する。
- A07：ノードが領域外へ消えず、移動後の接続線が正しく追従する。
- A08：映像未視聴なら動画QCはUNVERIFIED。

## 4. 実装・統合順序
- Phase 1：独立検証ブランチで資料適用範囲・承認分離の純粋関数と単体テスト。既存PR #20/#22/#23の履歴を改変しない。
- Phase 2：NodeDetails表示と操作安全性のテスト。架空テストデータのみ使用。
- Phase 3：CUT連続性のスキーマ・検証。実素材の同期や動画生成は対象外。
- Phase 4：PR差分・CI・表示を監督レビュー。マージ、本番デプロイ、MASTER昇格、公開はプロデューサーの最終判断。

## 5. 判定・残件
- PASS：既存コードと資料の読み取り監査、リスク整理、受入条件策定。
- CONDITIONAL：実装・単体テスト・ブラウザ確認・正史承認記録との照合。
- BLOCKED（MASTER昇格のみ）：正式承認scopeと実ファイル・映像QCが未確認。
- 未実施：GitHub書込、PR作成、OS/Obsidian同期、動画QC、課金、公開。
- 本書は監督DRAFTであり、承認済み規程や脚本原文の改訂ではない。

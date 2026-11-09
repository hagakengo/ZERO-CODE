# ZCS-DIRECTOR-CANVAS-BROWSER-QA-057 v0.1｜Canvas実ブラウザ受入試験

- ID: ZCS-DIRECTOR-CANVAS-BROWSER-QA-057
- Version: v0.1
- State: DRAFT / NOT EXECUTED
- Date: 2026-11-09
- PR: https://github.com/hagakengo/ZERO-CODE/pull/24
- Test target: Production Canvas検証画面（READ ONLY / TEST DATA）
- Related: ZCS-DIRECTOR-CANVAS-TEST-056 v0.1
- Guard: 正史・MASTER・本番反映・承認状態を変更しない。

## 前提条件

1. 対象PRの最新HEADでCI frontend/backend/dependency-auditを確認する。
2. ローカル検証または隔離プレビューで対象画面を開く。本番環境へのデプロイはしない。
3. 実際に画面を操作した人、日時、URL、ブラウザ、viewport、HEAD SHAを記録する。
4. この文書の作成自体はブラウザ試験の実施証拠にならない。

## 手動受入ケース

| ID | 操作 | 期待結果 | 状態 |
| --- | --- | --- | --- |
| BQA-01 | 画面を開く | READ ONLY / TEST DATA、架空の検証用データである旨を確認 | NOT RUN |
| BQA-02 | CUT 01を選択 | 前CUT参照が未設定のため比較UNVERIFIED。開始/終了状態未記録を表示 | NOT RUN |
| BQA-03 | CUT 02を選択 | 前CUT参照・順序根拠が未設定のため比較UNVERIFIED。NOT_FOUNDを未制作と断定しない | NOT RUN |
| BQA-04 | SCRIPT・SCENE・CHARACTER・ASSETを順に選択 | CUT固有欄を誤表示しない。関連ノードを正しく選択できる | NOT RUN |
| BQA-05 | 拡大・縮小・RESET・ノードドラッグ・背景パン | 操作が成立し、保存や外部API送信が発生しない | NOT RUN |
| BQA-06 | viewport 390pxで表示 | 横はみ出し、選択不能、操作不能がない | NOT RUN |
| BQA-07 | キーボードTab/Enterでノード選択 | フォーカス表示・操作が成立する | NOT RUN |
| BQA-08 | 認証・保存系の操作が存在しないことを確認 | MASTER/正史/承認状態を更新する導線がない | NOT RUN |

## 自動テストとの区別

- Node test / TypeScript / Next.js build / audit はCI検証であり、実ブラウザでの動作保証ではない。
- CUT比較は5項目の文字列比較。映像QC、同義語判定、演技・カメラの連続性保証ではない。
- CUT前後関係は明示的 previousCutId と sequenceEvidenceId、同一作品scope・SCENE・SCRIPTを要する。現在のサンプルデータでは前後関係は未指定。
- 本試験のPASS判定には各ケースの実施者・結果・証拠が必要。

## 判定

- Browser QA: BLOCKED（実ブラウザ検証環境へのアクセス未確保）
- Code/CI: commit 7e0fb5c24f58e0d8fb417819660863487fe07886、GitHub Actions run 42634834730。frontend / backend / dependency-audit は全て completed success。これはブラウザ実操作のPASSを意味しない。
- PR #24: open / Draft / mergeable、review threads 0件・review submissions 0件（2026-11-09照会時点）。レビュー未提出を承認済みと扱わない。
- Overall: CONDITIONAL。PRはDraft維持。

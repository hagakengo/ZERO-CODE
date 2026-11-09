# ZCS-DIRECTOR-CI-INCIDENT-062 v0.1｜PR24 CI不完全ジョブ調査

- ID: ZCS-DIRECTOR-CI-INCIDENT-062
- Version: v0.1
- State: DRAFT / INCIDENT OPEN
- Date: 2026-11-10
- PR: https://github.com/hagakengo/ZERO-CODE/pull/24
- Failed HEAD: 497c6caf7a86d2c2eec900a89ecb4a3145f837c2
- Workflow run: https://github.com/hagakengo/ZERO-CODE/actions/runs/42671051412

## 事実

- GitHub Actions run 42671051412 は completed / failure。
- 取得できたジョブは backend 129347440372 completed success、dependency-audit 129347441370 completed success の2件のみ。
- `.github/workflows/ci.yml` には frontend、backend、dependency-audit の3ジョブが定義されている。
- 当該runのジョブ一覧では frontend ジョブを取得できず、失敗ログと原因は未確認。
- `get_commit_combined_status` は statuses=[]。これはGitHub Actionsのジョブ結果に代わる成功証拠ではない。
- failed jobsの再実行要求はHTTP 403「This workflow run cannot be retried」。再実行成功とは扱わない。
- 直前HEAD 4b66e01961b17a788730b8efd61a71c134ee21ff のrun 42670204928 は frontend/backend/dependency-audit 全成功。
- その後の変更は `cut-sequence.ts` で空白付きノードIDを拒否する条件追加と、`production-canvas.test.cjs` の追加テスト4件。変更はPR Draftブランチ内に限定。

## 仮説（未確認）

- workflow/job作成・取得時のGitHub側の問題、またはfrontendの初期化失敗の可能性。
- テストや型チェックの失敗と断定する根拠は現時点でない。

## 次の安全な対応

1. このDRAFT文書を追加することで新しいPR HEADのCIを発火させ、frontendを含む3ジョブの生成・完了を照合する。
2. frontendが再び欠落または失敗した場合、GitHub Actions画面のrun/job詳細・失敗ステップ・ログを取得して原因を特定する。コード変更は根拠確認後に実施。
3. 新HEADのCIが成功してもブラウザBQA-01〜08、独立レビュー、承認は別ゲート。
4. マージ・本番デプロイ・MASTER・正史変更は実施しない。

## 判定

- CI: FAIL（原因未確定）。前HEADのPASSを現在HEADへ流用しない。
- Browser QA: BLOCKED / NOT RUN。
- Overall: CONDITIONAL（正式承認・マージ不可）。

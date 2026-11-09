# ZCS-DIRECTOR-LOCAL-CANVAS-QA-061 v0.1｜隔離ローカルCanvas検証手順

- ID: ZCS-DIRECTOR-LOCAL-CANVAS-QA-061
- Version: v0.1
- State: DRAFT / NOT EXECUTED
- Date: 2026-11-10
- Target: PR #24 https://github.com/hagakengo/ZERO-CODE/pull/24
- Related: ZCS-DIRECTOR-BROWSER-QA-EXECUTION-059 v0.1 / ZCS-DIRECTOR-PR24-RELEASE-GATES-060 v0.1
- Guard: 本番デプロイ・マージ・正史・MASTER・承認記録の変更禁止。

## ソース照合結果

- `frontend/app/production/canvas/page.tsx` は `/production/canvas` に対応。画面には `READ ONLY · TEST DATA` と架空データ注記がある。
- `frontend/app/production/canvas/ProductionCanvas.tsx` は sampleNodes / sampleEdges を利用し、表示位置とズームをReactローカルstateで保持する。
- `frontend/package.json`: Next.js 16.4.5、`dev`=`next dev`、`test:canvas`=`node --test tests/production-canvas.test.cjs`。
- 注意: `frontend/app/page.tsx`（トップDashboard）はAPI fetchやPOST同期/保存処理を含む。READ ONLY Canvasの検証対象ではない。トップページのボタンや同期操作を試さない。

## 前提と安全な起動手順（未実行）

1. 別の隔離作業ディレクトリで対象PRの最新HEADを取得し、`git rev-parse HEAD` でPR HEADと一致することを確認。既存の未コミット作業ツリーは触らない。
2. `cd frontend`。本番のAPIキー・DB接続情報・認証情報をコピーしない。既存の本番設定を変更しない。
3. `npm ci --no-audit --no-fund` を実行し、依存関係をロックファイルに従って準備。
4. `npm run test:canvas`、`npx tsc --noEmit` を実行。失敗したら証拠を記録して停止。
5. `npm run dev -- --hostname 127.0.0.1 --port 3100` でローカルのみ待ち受け。実際の起動ログとポートを確認。
6. ブラウザで **`http://127.0.0.1:3100/production/canvas` に直接アクセス**。トップDashboard `/` は開かず、同期・保存系APIに触れない。
7. BQA-059のBQA-01〜08を実施。Desktopと390px viewport、Tab/Enter、ズーム、ドラッグ、パン、RESETを確認。Networkの意図しない外部送信も確認する。
8. 証拠をBQA-059へ記録し、終了後に開発サーバーを停止。ローカルの試験用生成物を正式素材・正史として登録しない。

## 停止条件

- PR HEADが一致しない、想定外の環境変数や外部接続が必要、起動が127.0.0.1以外に公開される、依存インストールや型チェックに失敗した場合は停止。
- 画面の外部APIへのPOST等を確認した場合は停止して再現手順を記録。
- 既存Vercel `zero-code` はFastAPI設定・production READYであり、本手順の対象外。プレビュー/本番デプロイを作成しない。
- ブラウザ試験の実施者・日時・URL・HEAD・証拠が揃わなければPASSにしない。

## 現在の判定

- 実行: NOT EXECUTED（手順の文書化のみ）。
- 検証済みCI: HEAD 2f79dbff11c9a3c3b12260cd1eb39073cc67875a、run 42668465335、frontend/backend/dependency-audit 成功。
- Browser QA: BLOCKED、総合 CONDITIONAL。プロデューサーの正式承認未取得。

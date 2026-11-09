# ZCS-DIRECTOR-PR24-RELEASE-GATES-060 v0.1｜Canvas v2受入ゲート凍結案

- ID: ZCS-DIRECTOR-PR24-RELEASE-GATES-060
- Version: v0.1
- State: DRAFT / 未承認
- Date: 2026-11-10
- Target: https://github.com/hagakengo/ZERO-CODE/pull/24
- Related: ZCS-DIRECTOR-PR24-ACCEPTANCE-058 v0.1 / ZCS-DIRECTOR-BROWSER-QA-EXECUTION-059 v0.1
- Scope: 検証用READ ONLY Canvas。正式正史・映像MASTERの採用判断は含まない。

## 検証済みベースライン

- HEAD: a864c8eca8a6a85c5ad148b01502d0fce6021d84
- GitHub Actions: run 42664562554、frontend/backend/dependency-audit 全件 completed success
- frontend Canvas tests: 24 tests / 24 pass / 0 fail（CIログ照合）
- PR #24: Draft、レビュー提出0、review threads 0（直近の照会時点）
- ブラウザBQA-01〜08: NOT RUN。接続環境未確保。実操作PASSではない。

## 出荷前の必須ゲート（プロデューサーの正式承認とは別）

| Gate | 必須証拠 | 現状 | 判定 |
| --- | --- | --- | --- |
| G-01 | 最新HEADのCI frontend/backend/audit成功 | run 42664562554 | PASS |
| G-02 | CUT連続性比較が未確認・循環・参照欠落・scope違い・ID衝突で停止 | 自動テスト24件、文字列比較とUI静的検査 | CONDITIONAL（実ブラウザ未実施） |
| G-03 | BQA-01〜08、実施者・日時・URL・viewport・証拠ID | 実施票059に未実施と記録 | BLOCKED |
| G-04 | CUT比較MATCHを映像QCや承認済みと誤認させない | UI注記と静的テストあり、実画面未確認 | CONDITIONAL |
| G-05 | 根拠IDの実在性・権限・正史scope・時系列を独立確認 | 参照先未検証と明示 | BLOCKED（正式導入判断用） |
| G-06 | 独立レビューの提出・指摘への対応 | PR review 0 | BLOCKED |
| G-07 | プロデューサーの正式承認 | 未申請・未取得 | NOT APPROVED |

## 監督コードレビューで残る既知の限界

1. sequenceEvidenceId、boundary evidenceIdは非空文字列の検査のみ。資料の実在性・版数・承認権限は検証しない。
2. compareCutBoundariesは人物位置・姿勢・向き・小道具・カメラの文字列比較。映像の動き、演技、視線、フレーム接続を保証しない。
3. hasInconsistentPredecessorContextは同一SCENE/SCRIPTの連鎖だけを許可する。SCENEをまたぐ連続性は現仕様の対象外。正式仕様の変更はプロデューサー承認が必要。
4. hasAmbiguousNodeIdsは全ノードIDの重複・空欄でCUT比較を停止する。ノードデータ自体の修復、証拠の取得、MASTERの変更はしない。
5. 画面の関連ノード導線はID検索に依存。異常データ時の見た目と操作は実ブラウザ試験が必要。

## 作業停止ラインと次の工程

- 新たな再現可能な不具合・受入ゲートの不足が見つからない限り、追加の防御的機能開発を優先しない。
- 最優先: 接続されたブラウザで隔離プレビューを開き、実施票059にBQA-01〜08の証拠を残す。
- 次点: 独立レビュー、証拠IDの参照先確認、プロデューサーによる仕様と正式導入判断。
- ブラウザ試験ができない間はG-03をBLOCKEDのまま維持し、CI PASSを実画面PASSと表現しない。
- PR #24はDraft維持。マージ・デプロイ・正史・MASTER変更はしない。

## 総合判定

CONDITIONAL。自動テストはPASS、正式導入ゲートは未充足。


## 接続先実査（2026-11-10、監督追記）
- 最新検証済みHEAD: a0eea76478af527c5f2aeac3bf471257199f5e04、GitHub Actions run 42667864262。frontend/backend/dependency-audit 3ジョブ成功。
- Vercel接続先のread-only照会で、GitHub hagakengo/ZERO-CODE にリンクしたプロジェクト zero-code（project ID prj_utTJYuir1sRkAQmcrFqXkJAATCsM）を確認。
- 対象PRブランチ docs/director-canvas-gates-053-20261109 に絞った Vercel deployments検索は0件。対象HEADの隔離プレビューURLは確認できず、実ブラウザ試験の実行環境未確保。
- プロジェクトの直近デプロイにはmainのproduction READYが存在するが、これはPR #24の検証用デプロイではない。誤って本番をBQA対象にしない。
- プレビュー作成・本番デプロイ・マージは行っていない。G-03はBLOCKED、総合CONDITIONALを維持。
- 次の解消条件: 本番と隔離されたPR HEADのプレビュー/ローカル検証環境を確保し、BQA-059に実操作の証拠を記録する。
- この追記コミットのCIは別途確認が必要。


## Vercel設定照合：既存プロジェクトの用途不一致（2026-11-10）
- GitHub Actions: HEAD b4c10f90311d97e181656621043069bd719ff1c3、run 42668077796、frontend/backend/dependency-audit成功。
- Vercelの既存 zero-code プロジェクト（prj_utTJYuir1sRkAQmcrFqXkJAATCsM）をread-only照会。framework=fastapi、nodeVersion=24.x、最新デプロイtarget=production/READY、SSO保護有効。
- 対してPR #24のProduction Canvas画面は frontend/ 配下のNext.jsアプリ（frontend/package.json: next 16.4.5、scripts dev/build/start）。既存VercelプロジェクトをそのままPRプレビューに使っても、対象Next.js画面を検証できると確認できない。
- したがって既存zero-codeプロジェクトに対する手動プレビューデプロイは実行しない。FastAPI本番設定や環境変数、ルートディレクトリを変更しない。
- BQA-01〜08の解消手段は、隔離ローカルのfrontend Next.js起動、または専用の隔離Next.jsプレビュー環境の準備。環境の課金・公開範囲・認証・保存系APIの分離を確認してから実施する。
- 現時点でBQAはBLOCKED。プレビューのURL、実画面操作、ブラウザQA PASSは未確認。
- 本追記HEADのCIは別途確認する。

# ZCS-DIRECTOR-CANVAS-INTEGRATED-ACCEPTANCE-066 v0.1

- 状態: DRAFT / 監督レビュー記録
- 対象: ZERO CODE OS / Canvas v2 / Draft PR #35
- 作成日: 2026-11-10
- 関連: #24, #27, #29, #30, #32, #33, #34, #35, Issue #25, #31
- 正式承認: 未実施
- 正史・MASTER変更: なし
- 保存先: GitHubのPR #35 headブランチ（Obsidian/Dropbox保存は未検証）

## 1. 比較基準を混同しない

- PR #35 head: fix/canvas-isolated-navigation-035-20261110
- PR #35 base: docs/director-canvas-gates-053-20261109（PR #24 head）
- PR #35 base対比: ahead 26 / behind 0 / 8ファイル（2026-11-10確認）。
- main対比: ahead 112 / behind 0 / 28ファイル（2026-11-10確認）。Canvas v2以前の累積差分や依存・CI関連ファイルも含むため、PR #35だけをレビューしてmainへの直接反映を承認してはならない。
- PR #24 head対main: ahead 86 / behind 0 / 26ファイル。
- GitHub Actions run 42798034869: PR #35の旧HEAD 8002cd611d6fc0b5bc83ffb51ff2a52d766f2c18で3ジョブ成功。ただしbase変更前の実行。文書追加後のHEADは別途CI確認。

## 2. 統合PRの目的と適用範囲

- #35を#24のheadに向け、#27 node bounds、#29 前CUT参照ID検証（#30に統合）、#30 統合、#32 キーボード、#33 runtimeテスト、#34 方向ボタン、#35 Dashboard導線除去とpointer安全対策を単一PRでレビューする。
- #27/#29/#30/#32/#33/#34は履歴と比較用Draftとして維持。順不同にmainへ個別マージしない。
- 画面は架空TEST DATA専用。正史、実在素材、承認、MASTERに接続しない。

## 3. 受入マトリクス

| ID | 確認項目 | 判定 | 証跡・残作業 |
|---|---|---|---|
| INT-01 | PR #35のbase/head/差分確認 | PASS | GitHub PR metadata + compare（26コミット/8ファイル） |
| INT-02 | mainとの差分範囲の確認 | PASS | GitHub compare（112コミット/28ファイル）。直接mainへマージしない |
| CI-01 | 旧HEADの自動CI | PASS | GitHub Actions run 42798034869（base変更前） |
| CI-02 | 文書追加後の最新HEADのCI | NOT RUN | HEAD更新後に確認 |
| QA-01 | PC/390px実表示 | NOT RUN | 隔離ローカルQA |
| QA-02 | ドラッグ/パン/ズーム/RESET/境界 | NOT RUN | 実ブラウザと画面記録 |
| QA-03 | キーボード/方向ボタン/フォーカス | NOT RUN | Mac/browser shortcut競合も確認 |
| QA-04 | pointercancel/lostpointercapture/右クリック/複数ポインター | NOT RUN | 操作不能や誤移動がないこと |
| QA-05 | Network書込ゼロ、API/DB/承認操作なし | NOT RUN | DevTools通信ログ |
| QA-06 | 偽のMATCH/APPROVEDを作らない | NOT RUN | 欠落/循環/scope不一致/根拠不足 |
| GOV-01 | 正史/MASTER/承認状態の保護 | CONDITIONAL | コード上の架空データ隔離は確認、実ブラウザ副作用未検証 |
| REL-01 | プロデューサー正式承認 | NOT RUN | QAと統合方針確認後 |

## 4. 隔離QA手順

1. 元の未コミット作業ツリーを保護し、別ディレクトリにPR #35の最新HEADを取得する。
2. frontendで npm ci --no-audit --no-fund → npm run test:canvas → npx tsc --noEmit → npm run build。
3. npm run dev -- --hostname 127.0.0.1 --port 3100 で起動し、http://127.0.0.1:3100/production/canvas のみを開く。
4. PCと390px幅でQA-01〜06を実行。Networkで意図しない書込を確認したらBLOCKED。
5. 実行者・ブラウザ・画面幅・実結果・証跡を記録し、サーバーを停止する。

## 5. リリース判定と承認境界

現時点の総合判定: CONDITIONAL。自動CI成功は実ブラウザQAや実際の書込ゼロの証明ではない。Issue #25の過去のzero-job失敗の根本原因は未確定。Vercelの既存設定を無断変更しない。

マージ、production deploy、正史・MASTER変更、正式承認、課金はプロデューサーの別途判断を必要とする。個別Draftのクローズや承認状態変更も、レビュー記録と実体の整合を確認してから判断する。

# ZCS-DIRECTOR-BROWSER-QA-EXECUTION-059 v0.1｜Canvas実ブラウザ試験実施票

- ID: ZCS-DIRECTOR-BROWSER-QA-EXECUTION-059
- Version: v0.1
- State: DRAFT / NOT EXECUTED
- Date: 2026-11-10
- Scope: PR #24（https://github.com/hagakengo/ZERO-CODE/pull/24）/ Production Canvas READ ONLY TEST DATA
- Related: ZCS-DIRECTOR-CANVAS-BROWSER-QA-057 v0.1、ZCS-DIRECTOR-PR24-ACCEPTANCE-058 v0.1
- Guard: 本番デプロイ、マージ、正史・MASTER・正式承認状態の変更禁止。

## 実行前に記入（空欄のままPASSにしない）

- 実施者: NOT RECORDED
- 実施日時・タイムゾーン: NOT RECORDED
- 実施環境（隔離プレビュー/ローカル）: NOT RECORDED
- 検証URL（機密値は記載しない）: NOT RECORDED
- ブラウザ名・版: NOT RECORDED
- Desktop viewport: NOT RECORDED
- Mobile viewport: 390px（予定、実施未確認）
- PR HEAD SHA: NOT RECORDED
- CI run ID / status: 42660944950 / success（HEAD b0f520e0e08c434603d5dc43bd1734034ea4c075、2026-11-10確認。実行直前にHEADと再照合）
- 実施前データ状態（検証用であること）: NOT RECORDED

## BQA-01〜08 証拠採取欄

| ID | 実施手順と確認点 | 結果 | 証拠ID・画面/ログの保存先 | 実施者・日時 |
| --- | --- | --- | --- | --- |
| BQA-01 | 画面を開き READ ONLY / TEST DATA、架空データ注記を確認 | NOT RUN | 未取得 | 未記録 |
| BQA-02 | CUT 01選択。前CUT未指定・境界状態未記録で比較UNVERIFIED | NOT RUN | 未取得 | 未記録 |
| BQA-03 | CUT 02選択。順序根拠未指定でUNVERIFIED、NOT_FOUNDを未制作と誤認させない | NOT RUN | 未取得 | 未記録 |
| BQA-04 | SCRIPT、SCENE、CHARACTER、ASSETを選択。CUT欄なし、関連ノード遷移確認 | NOT RUN | 未取得 | 未記録 |
| BQA-05 | ズーム、RESET、ドラッグ、パン。保存・外部送信なしをNetwork等で確認 | NOT RUN | 未取得 | 未記録 |
| BQA-06 | 390px表示。横はみ出し、選択不能、操作不能なし | NOT RUN | 未取得 | 未記録 |
| BQA-07 | Tab/Enterでノード選択。フォーカス可視・操作可能 | NOT RUN | 未取得 | 未記録 |
| BQA-08 | 認証・保存・正史/MASTER/承認更新導線がないことを確認 | NOT RUN | 未取得 | 未記録 |

## 追加の異常系（自動テストと実ブラウザを混同しない）

- E-01: 自己参照、2ノード循環、3ノード以上の循環 → INVALID・比較停止（実画面 NOT RUN）。
- E-02: 前CUT参照先が欠落または非CUT → UNVERIFIED・比較停止（実画面 NOT RUN）。
- E-03: チェーン途中に別作品scope、別SCENE、別SCRIPT → UNVERIFIED・比較停止（実画面 NOT RUN）。
- E-04: 承認証跡のAPPROVEDに参照先・承認権限未検証の注記、根拠不足はUNVERIFIED（実画面 NOT RUN）。
- 追加の異常系を検証するために正史やMASTERへ試験データを書き込まない。必要なfixtureは隔離環境・未承認の架空データのみで用意する。

## 判定基準と引き継ぎ

- PASS: BQA-01〜08の全件実施・期待結果確認・証拠ID・実施者/日時・HEAD照合がそろう。異常系は別途結果を明記。
- CONDITIONAL: CIは成功しているが、実画面の証拠が未収集または一部欠落。
- BLOCKED: 実行環境にアクセスできない。接続失敗の事実のみを記録し、PASSにしない。
- FAIL: 実画面で期待結果に反する再現可能な事象を確認した場合。再現手順と証拠を保存し、修正は別コミットで実施する。
- 現時点: Browser QA BLOCKED / NOT EXECUTED、総合 CONDITIONAL。
- 接続障害: Browser接続は「originating browser context」が必要。接続拡張のあるブラウザでChatGPTと隔離検証画面を開き、再試行する。
- 試験PASSでも正式承認、MASTER採用、PRマージ、本番反映を自動実行しない。プロデューサー判断を別途求める。

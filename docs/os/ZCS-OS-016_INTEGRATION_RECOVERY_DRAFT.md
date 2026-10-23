# ZCS-OS-016｜Studio Memory隔離統合・復旧検証

状態：DRAFT／本番接続・正式記憶登録・PRマージなし。判定：**CONDITIONAL（隔離環境のみ）**。

## PR依存関係と統合方法

`main → #8 閲覧 → #9 Reader → #10 署名付き登録 → #11 鍵管理 → #12 DRAFT管理 → #13 Work間提出 → 本変更` の積み上げ構成。既存PR #8〜#13のブランチは変更しない。Readerの読み取り資格情報、提出専用資格情報、DRAFT管理用ローカル操作、人間署名は別の経路であり、Readerに書き込みAPIはない。共通の候補形式と私有Markdown保管庫を流用し、二重の承認モデルを作らない。将来はこの順序で各差分とCIを確認してから統合判断する。現段階でマージ・公開は不可。

```text
Work 02 --提出専用token--> loopback提出サービス --受付journal--> 私有原文コピー
                                      |                      |
                                      +----> DRAFT候補・注記 ----> 監督用packet
Reader token --> 読み取り専用Reader --> 私有正式Markdown保管庫
人間の署名経路 --> オフラインworkflow --> 合成鍵でのみ登録障害を検証
停止中の各保存先 --オフラインsnapshot--> 別の私有保存先（秘密鍵は除外）
```

## 今回の変更

- `backend/app/memory_workflow.py`：私有ファイルを一時ファイル、fsync、排他的リンクで確定。登録に排他ロックを追加。署名済みREGISTERED記録の直後に停止した場合、同じダイジェストの隠しstagingからのみ復旧可能にした。
- `backend/app/memory_drafts.py`：候補の注記を先に保存し、候補ファイルを最後の確定印とした。並列追加をロックし、途中で残った注記は隠しorphanとして保持する。
- `backend/app/memory_submission.py`：提出内容を私有transaction journalに確定してから原文・候補・受付を保存。起動時に未完了分を再実行し、全受付とDRAFT候補の整合性を確認。不一致なら起動を停止する。
- `backend/app/memory_backup.py`：提出、DRAFT、正式記憶、workflow、Reader認証状態を対象とするオフラインsnapshot。ファイル別SHA-256、前後の出典照合、単調増加sequenceで破損と古い復元を拒否。提出・Readerの対称鍵は含めず、復元先は新しい場所に限定する。
- `backend/tools/memory_submission.py`、`backend/tools/memory_workflow.py`、`backend/tools/memory_backup.py`：復旧・照合・snapshot用の管理CLI。既存のReader APIは変更なし。
- `backend/test_memory_recovery.py`、`backend/test_memory_workflow.py`：合成データ・合成鍵による障害注入と競合試験。

## 検証表

| 障害・競合 | 検証した結果 |
| --- | --- |
| 原文保存後、候補保存後、受付前、受付後で停止 | 私有journalから再実行し、受付とDRAFTが1件に収束 |
| 独立子プロセスを`os._exit(67)`で停止 | 再起動相当の別プロセスから復旧し、受付と出典がMATCH |
| 同一受付IDの並列・再送 | 1件の受付へ収束 |
| 別受付ID・同一候補ID | 内容一致は既存DRAFTを参照、内容不一致は拒否 |
| 候補保存中の一覧 | 未完成候補は表示されない |
| 監査書き込み障害 | 受付完了と表示されず、後の再試行で復旧 |
| 受付の出典SHA改変 | 起動時の全受付検査で停止 |
| 合成署名後の登録確定直前停止 | 署名・diff・stagingがすべて一致する場合だけ復旧 |
| 同一記憶IDの同時登録 | 1件のみREGISTERED、他方拒否 |
| 私有データsnapshot／復元 | 合成DRAFT・正式記憶・監査・公開鍵のバイト一致 |
| 古いsnapshot・破損snapshot | 復元を拒否 |
| Reader資格情報による提出、失効後提出、Work署名 | 既存境界の回帰テストで拒否 |

個別の故障点はテストで再現している。任意時点の電源断、ファイルシステムの破損、複数ホストでの同時運用は検証していない。

## 実候補の読み取り照合

`WORK02-EP00-R03-001`の実候補は読み取りのみ。候補SHA-256：`5d5d2ad535466e3b53cbee4d2fd16f9ebc309b71ac2eb6449e82f42616511886`。原文SHA-256：`1f238c05cb69cc2569b63b5c1aae33a07365356be8a7e5bffb32f6d8e14a47a7`。候補はDRAFT、技術QCはPASS、演出・作画QCはREWORK、本編MASTERと公開は未承認、正式記憶へは未登録。`YUNA-EYE-001`は関連する別記憶であり、上書き・統合しない。監督内容レビューは**REVIEW_HOLD推奨**だが、実候補には保存していない。監督署名・プロデューサー承認を意味しない。

今回、Work 02の独立チャットからの提出は再実施していない。#13での過去の成功と、今回の合成環境での復旧試験を区別する。

## 回帰・保全

隔離したバックエンドの`unittest discover`は130件PASS。フロントエンドの認証テストは9件PASS、TypeScriptチェックとNext.jsビルドもPASS。Draft PR #14の初回CIではbackend・frontendともPASS（GitHub Actions run `39999350633`）。本番OS `production.json` の作業前後SHA-256はともに`77a66760d4763aa4cfc138a60eb3794f3655bbc2b9d9ae1176aa11342f30e024`。実候補の作業前後SHA-256も同じ`5d5d2ad535466e3b53cbee4d2fd16f9ebc309b71ac2eb6449e82f42616511886`。

## 残存リスクと判定根拠

同じmacOSユーザーで動くWork同士のファイル権限は強い本人分離ではない。プロデューサー専用OSユーザーと実鍵の隔離・失効は未実施。バックアップは同一ユーザーがanchorとmanifestの両方を書き換えられる場合の悪意ある巻き戻りを防げない。snapshot取得中は全writerの停止が必要で、復元後は絶対パスの再設定と新しいサービス資格情報が必要。公開鍵台帳の更新と署名検証の並行性、監査媒体そのものの破損、電源断の全タイミングは追加検証が必要。

したがって、合成データによる隔離復旧の基礎機能は動作したが、継続的な実運用や本番移行は**CONDITIONAL**。次は別OSユーザーによる拒否試験、backup anchorの外部保護、鍵台帳更新の原子性、実機相当の障害試験を行い、プロデューサーが運用開始を判断する。

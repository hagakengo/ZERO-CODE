# ZCS-SNS-OPS-003 本番限定導入・復旧手順（未適用）

## 導入前ゲート

1. 本番 `DATABASE_URL` と実行主体を確認する。値そのものは報告書・ログへ出さない。
2. `BUFFER_API_KEY`、`SNS_WRITE_TOKEN` を本番の秘密管理へ登録し、Gitやログに含めない。
3. SQLiteの場合はサービス停止または書込停止後、`tools/backup_sqlite.py` で一貫したバックアップとSHA-256を作る。PostgreSQLの場合は管理基盤のスナップショットまたは `pg_dump` を利用する。
4. バックアップから隔離DBを復元し、起動・全回帰・SNS E2Eを通す。
5. 初回は `SNS_AUTO_SCHEDULE_ENABLED=0`、`SNS_AUTO_REFRESH_ENABLED=0` とする。
6. アプリだけを限定反映し、`social_posts` と `social_post_attempts` が追加されたこと、既存テーブルが不変であることを確認する。

SNS用テーブルはSQLAlchemyの `CREATE TABLE IF NOT EXISTS` 相当で追加される。既存列の変更や削除は行わない。

### PostgreSQLバックアップ・復元ゲート

Neonの管理スナップショットが利用可能ならそれを第一選択とする。手動取得では、秘密値をコマンド引数・ログ・報告書へ出さず、権限を`0700`にした作業ディレクトリと`0600`の`PGPASSFILE`を使用する。

1. 自動処理を停止し、対象project/branch/databaseを識別値で再確認する。
2. `pg_dump --format=custom`で全DBを取得し、SHA-256、サイズ、取得日時、対象識別子を別manifestへ記録する。
3. Productionとは別の隔離DBを新規作成する。
4. `pg_restore --clean --if-exists`で隔離DBへ復元する。
5. source/restoreのpublic table数、`social_posts`、`social_post_attempts`、既存主要テーブルの件数を比較する。
6. 復元DBに対して全回帰試験とSNS dry-runを行う。
7. 検証用資格情報と復元DBを破棄し、バックアップはアクセス制御された保存先へ移す。

接続先、資格情報、バックアップのいずれかを確認できない場合は本番移行をHOLDする。復元未検証のバックアップを復旧可能とは報告しない。

## 限定検証

1. `tools/sns_ops.py detect` で候補だけを確認する。
2. 既存Buffer Queue、Sent、Xと比較し、二重投稿がないことを確認する。
3. 手動 `refresh` で既存予約の追跡を確認する。
4. 自動実行はOFFのまま、`run-detect` と `run-refresh` がそれぞれdry-run／skippedになることを確認する。
5. プロデューサーの最終承認後だけ、必要なフラグとスケジューラーを段階的に有効化する。

## 定期実行

`ops/sns-ops.cron.example` は設定例であり、リポジトリ内に置くだけでは稼働しない。日次検出は毎日09:00 JST、公開照合は月水金20:15 JST。GitHub Actions、Vercel Cron、OS cronのいずれか一つだけを選び、重複実行を避ける。

## ロールバック

1. スケジューラーを停止し、両自動フラグを `0` に戻す。
2. 直前リリースへアプリを戻す。SNS用テーブルは監査証拠保全のため削除しない。
3. SNS処理による既存投稿の変更は行わない。Buffer/Xの実状態を先に確認する。
4. DB破損がある場合のみ、サービスを停止し、バックアップのSHA-256を照合して全DBを復元する。復元前DBも別名で保全する。
5. 復元後、既存機能の回帰試験とnote/Buffer/Xの読み取り照合を行う。

DB全体の復元はSNS以外の新しい変更も巻き戻すため、最後の手段とする。SNS用テーブルだけの削除や履歴改変を通常のロールバックとして行わない。

# ZCS-SNS-OPS-002 運用手順（DRAFT）

## 状態と境界

ZERO CODE STUDIOの公開済みnote記事を検出し、通常告知をBufferへ予約し、BufferとXの公開証拠をOS台帳へ反映するための手順である。未公開情報、機密情報、未検証の承認・MASTER主張、重要発表は自動対象外でHOLDとする。

予約成功は `SCHEDULED`、Xの `@sora1993xny` 投稿URLを取得できた場合のみ `PUBLISHED` とする。予約IDや公開URLを推測しない。

## 必要な環境変数

- `NOTE_RSS_URL=https://note.com/sora199312/rss`
- `BUFFER_API_KEY`（ログやGitへ保存しない）
- `BUFFER_X_CHANNEL_ID`（複数のXチャンネルがある場合）
- `SNS_WRITE_TOKEN`（OSの変更API用。ログやGitへ保存しない）
- `ZERO_CODE_OS_URL`（CLIの接続先。省略時はローカル）

## 操作

```bash
cd backend
python tools/sns_ops.py detect   # 読み取り・予約候補確認のみ
python tools/sns_ops.py apply    # 未告知の通常記事を次の月水金20時枠へ予約
python tools/sns_ops.py refresh  # Buffer結果を照合。X URLがある場合のみ公開済みにする
python tools/sns_ops.py run-detect  # 定期実行用。初期設定では必ずdry-run
python tools/sns_ops.py run-refresh # 定期実行用。初期設定ではskipped
```

`apply` はnote URLを一意キーとしてDBロック下で処理し、Bufferにも本文・予約日時が同一の投稿がないか事前照合する。失敗時は `FAILED`、Buffer未接続時は `HOLD` となる。再試行は `/api/sns/posts/{post_id}/retry` を使い、Buffer重複検査後に履歴を記録する。

## 継続監視

推奨周期は、記事検出を毎日09:00 JST、公開結果照合を月・水・金20:15 JSTに実行すること。現時点ではスケジューラーを本番へ有効化していない。`SNS_AUTO_SCHEDULE_ENABLED=0` と `SNS_AUTO_REFRESH_ENABLED=0` が初期値であり、定期実行用コマンドは予約・台帳更新を行わない。既存の信頼できる実行基盤へ一系統だけ登録し、接続先・秘密情報・実行主体を確認してから段階的に有効化する。

## 障害復旧

1. `FAILED` の本文、URL、予定日時、エラーを確認する。
2. Buffer Queue/SentとXを先に確認し、重複がないことを確認する。
3. retry APIを1回実行する。Bufferに同一投稿があれば既存IDへ関連付ける。
4. `refresh` で状態を再照合する。
5. X URLを自動取得できない場合は、実在する `https://x.com/sora1993xny/status/<数字>` のみ確認APIへ渡す。

DB復元時は `social_posts` と `social_post_attempts` を同じ時点へ戻す。既存の制作承認台帳、MASTER、`production.json` は本機能の対象外である。

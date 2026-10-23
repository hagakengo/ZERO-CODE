# ZCS-OS-017｜制作連携パイロット検証結果

状態：DRAFT／隔離環境。実制作記憶の正式登録・本番接続なし。

## 変更ファイル

`backend/app/memory_brief.py`、`backend/tools/memory_brief.py`、`backend/tools/memory_review_brief.py`、`backend/test_memory_brief.py`、本設計・検証文書。既存Reader・認証・DRAFT提出・ワークフローのコードは変更していない。

## 実接続と成果物

- Work 02独立チャットから127.0.0.1の隔離Readerへ、Work 02専用の短命資格情報で接続。検索2件・詳細1件が全てHTTP 200。`YUNA-EYE-001`をDRAFTとして取得。Work 02自身が制作開始ブリーフを私有Markdown/JSONへ保存した。約2.40秒はWork 02の報告値。
- Work 01は取得結果と私有DRAFTレビューpacketのSHAを照合し、監督用ブリーフを保存。技術QC PASS、演出・作画QC REWORK、監督内容レビューREVIEW_HOLD推奨、MASTER・公開・正式記憶登録は未承認。
- 私有証拠のSHA-256：制作開始JSON `2f1a718f72b05446a1db69a70e2631f5d6459917e49c53a25ff9180671d64d23`、監督用JSON `88c5658bbe102f63e5734bef2c5c59f6fd2d0d8f5e85ebd4be2a2a518412c3ae`、独立接続証拠 `34995b1302503d3c95d83fccc15cec7a9fc319db151fa0788cd8f76ffbcefc78`。
- `YUNA-EYE-001`の関連ID `STUDIO-WORKFLOW-001`は一覧メタデータにあり、詳細は未取得。出典は論理参照であり、参照先全原本の再照合は今回行っていない。

## 異常系

| ケース | 隔離Reader／テスト結果 |
| --- | --- |
| 認証なし、期限切れ、個別失効 | HTTP 401 |
| 不存在記憶ID | HTTP 404 |
| 該当なしの検索 | HTTP 200、count 0。接続失敗とは区別 |
| DRAFTの承認済み限定詳細 | HTTP 404 |
| Work 01の承認済み限定検索 | 目元についてcount 0 |
| K07の承認範囲 | `APPROVED`はX02＋K07のSNS公開のみ、本編MASTER含まず |
| Reader検索と詳細の不一致／approved-only資格情報の誤用 | ブリーフ生成を拒否する単体テストPASS |
| DRAFTをAPPROVEDとしたreview packet | 監督ブリーフ生成を拒否する単体テストPASS |

Reader監査は12イベントを確認し、記憶本文とBearer文字列は含まれなかった。資格情報の値はチャット・Gitに出していない。隔離コピー3件のSHAは元ファイルと全件一致。ブリーフは0600。既存の実候補は読取のみで、`source_state=MATCH`、`review_status=REVIEW_PENDING`を再確認した。

## 回帰と保全

ローカルbackend全体137件PASS（新規ブリーフ7件を含む）。frontend認証9件PASS、TypeScriptチェック、Next.jsビルドPASS。Draft PRのCIは作成後に確認する。本番OS `production.json` の開始時・終了時SHA-256はともに`77a66760d4763aa4cfc138a60eb3794f3655bbc2b9d9ae1176aa11342f30e024`、実候補も両時点で`5d5d2ad535466e3b53cbee4d2fd16f9ebc309b71ac2eb6449e82f42616511886`。試験後に隔離Readerを停止し、隔離環境のWork 01・02資格情報を失効、tokenファイルを削除した。

## 判定

**隔離制作連携パイロット：PASS。正式運用開始：未承認／条件未達。** Work 02独立チャットから実際に読め、制作開始と監督レビューの資料を生成した。一例で制作負担や手戻りの削減は実証していない。元保管庫の権限、同一macOS UIDでの資格情報隔離、実鍵、バックアップ巻き戻り防止、復元後再結線が残る。Readerサービスの外部公開、本番OS接続、PRマージは行わない。

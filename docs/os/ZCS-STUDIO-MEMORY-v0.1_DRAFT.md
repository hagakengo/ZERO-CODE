# Studio Memory v0.1 — DRAFT

Studio Memoryは[閲覧専用MVP](ZCS-OS-WEB-MVP_IMPLEMENTATION_DRAFT.md)の独立した、レビュー済みMarkdownノートの閲覧口。既存のローカルZERO CODE OS `production.json`、SQLite、MASTER、Draft PR #8のスナップショットを読み書きしない。PR #8から分岐した隔離ブランチで実装した。公開環境・本番3128へは接続しない。

## 保存形式と承認境界

- 初期記憶ノートは**公開GitHubリポジトリの外**にある非公開保管庫に保存する。Obsidianで開けるMarkdownで、YAML 1.2の一部であるJSON引用文字列とフロー配列をfrontmatterに使う。`[[MEMORY-ID]]`で相互リンクする。公開リポジトリには実ノートをコミットしない。
- 必須フィールド：`id`、`title`、`kind`、`approval_status`、`approval_scope`、`source`、`sources`、`updated_at`、`related`、`assets`。出典には指示書ID、リポジトリ内文書、ローカル審査資料の論理参照を記す。端末の絶対パスや秘密はノートに入れない。
- `approved_only=true`は`approval_status: APPROVED`だけを返す。承認範囲は`approval_scope`で明示し、SNS公開承認を本編MASTER承認へ拡張しない。DRAFT／CANDIDATE／REWORK／UNVERIFIEDは正式判断検索から除外する。
- ノートの追加・変更はGit上の提案と人間のレビューで行う。APIに書き込み、承認自動化、原本自動インポートはない。出典不明や記録の食い違いは本文に残す。
- 初期3件のうち、目元判断と制作役割はDRAFT。SNS公開判断はその公開範囲のみAPPROVED。実ノートの出典と未照合事項は非公開保管庫で管理する。

## AIチーム向け読み取り

既存Readerと同じ`STUDIO_READER_TOKEN`で認証する。`STUDIO_MEMORY_DIR`に**非公開保管庫**の絶対パスを設定し、隔離されたローカルReaderを起動する。設定がない場合は503で閉じる。Next.jsの認証済みBFFは`/api/studio/memory/*`のみ中継し、既存セッションが失効したら401を返す。外部公開用認証は未実装。

| 用途 | GET |
| --- | --- |
| キーワード検索 | `/api/studio/memory/search?q=ユナの目元` |
| 正式判断のみ | `/api/studio/memory/search?q=K07&approved_only=true` |
| 記憶詳細 | `/api/studio/memory/K07-PUBLICATION-001` |
| 正式判断の詳細 | `/api/studio/memory/K07-PUBLICATION-001?approved_only=true` |

検索結果はID、種別、出典、承認状態・範囲、更新日、関連ID、素材IDを返す。詳細は本文も返す。検索は全角半角を正規化し、空白区切り語のAND検索。ノートは最大32 KiB、未知のfrontmatterキー・壊れた形式・シンボリックリンクを拒否する。ノート本文は認証済みの内部利用に限る。生成AI用の一般公開エンドポイントやMCPサーバーは提供しない。

Work 01・02の作業開始時には対象語で検索し、詳細の`approval_status`と`approval_scope`、`sources`を確認する運用を想定する。**別チャットのWork 01・02から実際に取得したことは未検証**。利用には両Workの実行環境からローカルReaderへ安全に接続する設定が必要。認証情報をチャットやGitに記載しない。

## Obsidianでの閲覧

Obsidianの「フォルダーを保管庫として開く」で`STUDIO_MEMORY_DIR`に指定した非公開保管庫を選ぶ。Obsidianを使わなくても任意のMarkdown閲覧ソフトで読める。ノート編集が即時に本番OSやMASTERへ反映される仕組みはない。

## 検証と残課題

`backend/.venv-reader/bin/python -m unittest -v test_studio_memory test_studio_reader`は隔離した一時ノートと既存Readerの一時スナップショットだけを使う。`frontend`では`npm run test:studio`と`npm run build`。実データへの書き込み、外出先アクセス、実機スマホ、AIチームの別チャットからの接続、MCP公開、原文資料インポートは未実施。

次段階は、ノート変更提案のレビュー導線、出典への安全なリンク解決、複数Work環境からの非公開アクセス設計。外部公開時は既存PR #8の認証・HTTPS・監査・レート制限の未解決条件を先に満たす。

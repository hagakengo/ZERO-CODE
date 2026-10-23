# Studio Memory v0.1 — DRAFT

Studio Memoryは[閲覧専用MVP](ZCS-OS-WEB-MVP_IMPLEMENTATION_DRAFT.md)の独立した、レビュー済みMarkdownノートの閲覧口。既存のローカルZERO CODE OS `production.json`、SQLite、MASTER、Draft PR #8のスナップショットを読み書きしない。PR #8から分岐した隔離ブランチで実装した。公開環境・本番3128へは接続しない。

## 保存形式と承認境界

- 初期記憶ノートは**公開GitHubリポジトリの外**にある非公開保管庫に保存する。Obsidianで開けるMarkdownで、YAML 1.2の一部であるJSON引用文字列とフロー配列をfrontmatterに使う。`[[MEMORY-ID]]`で相互リンクする。公開リポジトリには実ノートをコミットしない。
- 必須フィールド：`id`、`title`、`kind`、`approval_status`、`approval_scope`、`source`、`sources`、`updated_at`、`related`、`assets`。出典には指示書ID、リポジトリ内文書、ローカル審査資料の論理参照を記す。端末の絶対パスや秘密はノートに入れない。
- `approved_only=true`は`approval_status: APPROVED`だけを返す。承認範囲は`approval_scope`で明示し、SNS公開承認を本編MASTER承認へ拡張しない。DRAFT／CANDIDATE／REWORK／UNVERIFIEDは正式判断検索から除外する。
- ノートの追加・変更はGit上の提案と人間のレビューで行う。APIに書き込み、承認自動化、原本自動インポートはない。出典不明や記録の食い違いは本文に残す。
- 初期3件のうち、目元判断と制作役割はDRAFT。SNS公開判断はその公開範囲のみAPPROVED。実ノートの出典と未照合事項は非公開保管庫で管理する。

## AIチーム向け読み取り

記憶APIは既存素材Readerの`STUDIO_READER_TOKEN`から独立した、Work別の短命署名トークンを検証する。`STUDIO_MEMORY_DIR`に**非公開保管庫**、`STUDIO_MEMORY_AUTH_DIR`にGit管理外の秘密ディレクトリを指定する。未設定・破損時は503で閉じる。Next.jsの認証済みBFFは記憶API用に`STUDIO_MEMORY_WEB_TOKEN`を別途使い、セッション失効時は401を返す。Web用トークンは承認済み記憶だけを取得できる。外部公開用認証は未実装。

| 用途 | GET |
| --- | --- |
| キーワード検索 | `/api/studio/memory/search?q=ユナの目元` |
| 正式判断のみ | `/api/studio/memory/search?q=K07&approved_only=true` |
| 記憶詳細 | `/api/studio/memory/K07-PUBLICATION-001` |
| 正式判断の詳細 | `/api/studio/memory/K07-PUBLICATION-001?approved_only=true` |

検索結果はID、種別、出典、承認状態・範囲、更新日、関連ID、素材IDを返す。詳細は本文も返す。検索は全角半角を正規化し、日本語の文字種と英数字IDを分けたキーワードAND検索。自然文の意味解析や同義語検索ではない。ノートは最大32 KiB、未知のfrontmatterキー・壊れた形式・シンボリックリンクを拒否する。ノート本文は認証済みの内部利用に限る。生成AI用の一般公開エンドポイントやMCPサーバーは提供しない。

Work 01・02の作業開始時には対象語で検索し、詳細の`approval_status`と`approval_scope`、`sources`を確認する。Work 01は承認済み記憶のみ、Work 02はDRAFTを含む読取権限を持つ。共通の承認済みK07記憶は双方から取得可能。2026-10-23のZCS-OS-010では別Workチャットからの取得を実証したが、当時のトークンは共有型であり失効・監査は未実装だった。接続テストはローカル同一ホスト上に限る。

## Work別認証と監査（ZCS-OS-011）

- 管理操作は`backend/tools/memory_auth.py`のみ。`init`で秘密ディレクトリを明示作成し、`issue`で最大900秒の短命資格情報を0600の新規ファイルへ発行する。`revoke-token`は1資格情報、`revoke-work`は対象Workの既発行資格情報だけを失効する。APIには発行・失効・書込の経路がない。
- `work01`はAPPROVED限定、`work02`は全状態、`web`はAPPROVED限定。いずれも検索・詳細取得だけ。発行時には操作をさらに検索だけに制限できる。APIは署名、有効期限、Work別世代、操作・承認範囲を毎回確認する。
- 読取監査はUTC時刻、Work識別子、操作（検索／詳細）、HTTP結果のみを私有JSONLに追記する。本文・検索語・記憶ID・URL・IP・資格情報は記録しない。監査を書けない場合は503にする。認証に失敗した場合はWorkを推定せず`unknown`とする。
- 秘密ディレクトリは0700、秘密ファイルは0600、同一ユーザー所有を要求する。Git・チャット・PRへ資格情報や記憶本文を載せない。同じmacOSユーザーIDを共有する別Work間ではOSファイル権限だけで相互秘匿できない。端末が異なるWork・外出先アクセスは未対応で、別ID分離・秘密配布・HTTPS・レート制限・集中監査を設計してから接続する。

安全なローカル再接続手順：`backend`を作業ディレクトリとし、管理者がGit外の秘密ディレクトリで`.venv-reader/bin/python -m tools.memory_auth --auth-dir <秘密ディレクトリ> init`を一度だけ実施する。各Workの作業直前に同じコマンドの`issue --work work01|work02 --access approved|all --ttl 300 --out <専用のGit外ファイル>`で別々に発行し、資格情報本文を表示せず専用ファイルをそのWorkに渡す。WorkはReaderのループバックURLへ検索し、詳細の`approval_status`・`approval_scope`・`sources`を確認する。期限切れなら新規発行し、旧資格情報を破棄する。漏えい疑いは対象Workの`revoke-work`で即時失効させる。接続不能時は共有済みと報告しない。Browser BFFのWeb用資格情報も同様に短命で、手動更新が必要。Reader起動時は一般アクセスログに検索語を残さないよう`--no-access-log`を指定する。

## Obsidianでの閲覧

Obsidianの「フォルダーを保管庫として開く」で`STUDIO_MEMORY_DIR`に指定した非公開保管庫を選ぶ。Obsidianを使わなくても任意のMarkdown閲覧ソフトで読める。ノート編集が即時に本番OSやMASTERへ反映される仕組みはない。

## 検証と残課題

`backend/.venv-reader/bin/python -m unittest -v test_studio_memory test_studio_reader`は隔離した一時ノートと既存Readerの一時スナップショットだけを使う。`frontend`では`npm run test:studio`と`npm run build`。実データへの書き込み、外出先アクセス、実機スマホ、MCP公開、原文資料インポートは未実施。

次段階は、ノート変更提案のレビュー導線、出典への安全なリンク解決、複数Work環境からの非公開アクセス設計。外部公開時は既存PR #8の認証・HTTPS・監査・レート制限の未解決条件を先に満たす。

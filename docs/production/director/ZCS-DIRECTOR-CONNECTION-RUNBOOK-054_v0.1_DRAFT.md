# ZCS-DIRECTOR-CONNECTION-RUNBOOK-054 v0.1｜監督接続・保存・復旧手順

- Document ID: ZCS-DIRECTOR-CONNECTION-RUNBOOK-054
- Version: v0.1
- Status: DRAFT / 監督運用手順（接続確認範囲のみ）
- Date: 2026-11-09
- Related: ZCS-DIRECTOR-CANVAS-GATES-053 v0.1; ZCS-GOV-APPROVAL-001 v1.1
- Scope: ZERO CODE STUDIO / ZERO CODE OS（別案件のSNS・アフィリエイトとは分離）

## 1. ZERO CODE OS / GitHub

- Repository: `hagakengo/ZERO-CODE`（GitHub connector `mcp__GitHub__*`）
- Read: `fetch_file({repository_full_name,path,ref})`; PRは `get_pr_info({repository_full_name,pr_number})`; 差分は `compare_commits({repo_full_name,base,head})`。
- Write: `create_branch({repository_full_name,branch_name,sha})` → `create_file({repository_full_name,path,content,message,branch})` または `update_file({repository_full_name,path,content,message,sha,branch})`。
- `update_file` の `sha` は、対象ブランチの `fetch_file` で取得した**ファイルblob SHA**。コミットSHAと混同しない。
- Verify: 対象ブランチから `fetch_file` で再取得 → 内容照合 → `compare_commits` で変更ファイル・行数・起点を確認。書き込み結果のみでPASSにしない。
- Proven validation branch: `docs/director-canvas-gates-053-20261109`; starting SHA `4c95a6a4357335942acc94afd8bfd407e60879e5` (PR #23 HEAD at creation); latest verified commit `51dda7b9a667e37fe46a7aa8302e121b351f4555`。
- Proven write: `docs/production/director/ZCS-DIRECTOR-CANVAS-GATES-053_v0.1_DRAFT.md`。同ブランチで `NodeDetails.tsx` の未確認表示と `production-canvas.test.cjs` の回帰テストを更新。テスト実行は未確認。
- Safety: 既存作業ツリー、main、既存PR #20/#22/#23、正史、MASTERを無断変更しない。ブランチでのコミットは本番OSへの反映を意味しない。

## 2. Dropbox

- Connector: `mcp__Dropbox__*`。
- Existing files: `search({query})` → `get_file_metadata({path_or_file_id})` → 対応形式なら `fetch({id})`。
- New Paper: `paper_create_document({title})` → `paper_read_document({docRef})` → revisionを指定して `paper_apply_markdown({docRef,baseRevision,bodyMarkdown})` → `paper_read_document` で内容と新revisionを再検証。
- Proven Paper: `id:yqPbZD8BxvAAAAAAAAAAjg` / `ZCS-DIRECTOR-CANVAS-GATES-053 v0.1｜監督統合監査・実装指示 DRAFT` / verified revision 1。
- PaperとGitHubの複製は別保存物。片方の更新が自動で他方に同期されると仮定しない。
- 注意: PNGはメタデータ取得ができても、`fetch` で内容を抽出できない場合がある。画像視覚QCやSHA検証は別手段が必要。

## 3. Obsidian / 本番OS

- Obsidianの直接書き込み・同期は未検証。DropboxやGitHubへの保存をObsidian保存済みと表現しない。
- 本番OSのDB書き込み・Web UI反映・本番デプロイも未検証。GitHubの検証ブランチへの保存を本番反映と表現しない。
- 必要時は接続先、権限、保存パス、再読込結果を確認してから運用拡張する。

## 4. 復旧・引き継ぎ

1. 本書をGitHub検証ブランチから読み、文書ID・版・DRAFTを確認。
2. 接続ツールが見つからなければ利用可能なGitHub/Dropboxコネクタを再発見。接続状態は都度確認し、過去の成功だけで現時点の権限を断定しない。
3. 保存前に対象ブランチとSHAを再取得し、既存承認済みファイルと衝突しないパスを使う。
4. 保存後は再取得と差分確認。失敗・未確認はBLOCKEDまたはCONDITIONALと記録。
5. 正史・脚本・MASTERの承認変更、マージ、本番公開、課金はプロデューサーの最終判断。

## 5. 判定

- PASS: GitHub独立ブランチ作成、DRAFT文書保存・再取得、Dropbox Paper保存・再読込。
- CONDITIONAL: GitHubのコード変更のテスト実行、OS本番画面反映、Obsidian同期、画像実内容の検証。
- この文書自体は監督DRAFTであり、プロデューサー承認済みの規程ではない。

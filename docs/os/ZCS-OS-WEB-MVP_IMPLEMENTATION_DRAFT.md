# ZERO CODE OS 閲覧専用Web MVP — 実装・調査・運用（DRAFT）

基準日：2026-10-23。監督レビュー待ち。本番公開・本番移行・書き込み有効化の承認ではない。

## 調査結果

GitHub main基準コミットは8db52c6。Next.js/React/TypeScript、FastAPIと運営指標のSQLite実装が存在する。一方、ローカル版にはGitHub mainにない制作JSON台帳・編集API・原稿リーダー・Basic認証がある。両者を同一の保存先・実装と扱わない。

現行のローカル制作台帳はrevision 35、素材71件、履歴41件。元の68件と、ユナ第一原画r02 K05/K07/K08の表情作画参考候補3件を確認した。JSONのSHA-256は77a66760d4763aa4cfc138a60eb3794f3655bbc2b9d9ae1176aa11342f30e024。既存素材ID・全履歴・承認状態を保持した閲覧コピーを作成する。既存SQLiteの本番接続先は未照合であり、アプリを起動して推測接続しない。本MVPは制作JSONの読取を使い、SQLiteへ接続しない。

旧D1/匿名フード主人公のルールは旧企画の参照として保持。現行EP00ユナの正史へ転用しない。映像基準ZCS-VISUAL-001は画風の方向性であり、顔のMASTER承認とは別。

## 接続・保存設計

1. 運用者が非公開設定で制作JSONと素材ルート、版ごとのレビュー用パッケージを明示する。
2. `backend/tools/build_studio_snapshot.py`を明示実行し、**新規の非公開ディレクトリ**にmanifest・閲覧用コピー・原本照合レシートを作る。起動時の自動同期やDB移行はしない。
3. 元台帳の前後SHA、IDの一意性、コピー元・コピー先のSHAを検証する。対象外形式・許可ルート外・取得不能・容量制限超過は代替せず「未取得／閲覧コピー未作成」。
4. ブラウザはNext.jsだけに接続する。HttpOnly/SameSite=Strictの署名付き6時間セッションをサーバーで検証し、FastAPI向けBearerトークンはブラウザへ渡さない。
5. FastAPIは独立した閲覧専用エントリーポイント`app.studio_reader:app`を使う。既存の更新・指標・外部同期APIはこのサービスに登録しない。
6. 許可された論理IDだけで素材を要求する。任意ファイルパス・任意URLを要求できない。コピーは配信直前にもSHAを照合し、逸脱・シンボリックリンク・改ざんは拒否する。
7. PNG/JPEG/MP4と明示したテキスト資料のみ配信。HTML/SVGは非対応。動画Range GET/HEADをサポート。全応答はprivate/no-store、nosniff。

閲覧DTOにはMac絶対パスを出さず、論理ID、出典、ハッシュ、private-copy://保管先を示す。原本の絶対パスと照合レシートは非公開領域だけに保持する。公開Gitへ素材・manifest・実データ・認証情報を追加しない。

## 画面

- `/production`：登録件数、REWORK、レビュー待ち、現在カットの承認未確認、制作中エピソード、最近の実履歴、source revision、コピー取得時点。
- `/production/cuts/ep00-yuna-rain`：第一原画r01〜r03、実MP4、24原画、拡大、2版比較、タイムシート・QC、次工程保留。
- `/production/library`：元71素材のIDと状態、検索・案件フィルター、実素材、未取得表示、出典・ハッシュ。K05/K07/K08は表情参考候補であり完成原画・MASTERではない。
- `/production/reviews`：監督のr02静止画レビュー、Work自己QCを別出典として表示。r02動画の監督合格は未確認。
- `/production/login`：単一閲覧者のローカル検証用ログイン。承認・編集・公開ボタンなし。

レビュー資料がない版を番号だけでREWORKと推定しない。自己QC資料中のREWORK記載が確認できない版はUNVERIFIED。PASSやMASTERへ自動昇格させない。

## 隔離環境の起動

Python 3.12以上。既存の全backend依存には環境依存DBドライバーが含まれるため、閲覧専用の最小依存を分離した。元requirements.txtは変更しない。

```sh
cd backend
python3.12 -m venv .venv-reader
.venv-reader/bin/pip install -r requirements-reader.txt
.venv-reader/bin/python -m unittest -v test_studio_reader
```

非公開の設定例（ファイルそのものはGitに保存しない）：

```json
{
  "production_file": "<private-production-json>",
  "media_roots": ["<private-media-root>"],
  "packages": [
    {"version": "r01", "path": "<private-r01-package>"},
    {"version": "r02", "path": "<private-r02-package>"},
    {"version": "r03", "path": "<private-r03-package>"}
  ],
  "max_file_bytes": 30000000
}
```

```sh
backend/.venv-reader/bin/python backend/tools/build_studio_snapshot.py \
  --config /private/operator-config.json --destination /private/NEW-snapshot
```

設定するサーバー環境変数：

- `STUDIO_SNAPSHOT_DIR`：FastAPIだけで使用する非公開コピー先。
- `STUDIO_READER_TOKEN`：32文字以上。Next.jsとFastAPI間だけで共有する。
- `STUDIO_READER_URL`：Next.jsから見たFastAPI。検証例はhttp://127.0.0.1:8135。
- `STUDIO_VIEWER_USER`、`STUDIO_VIEWER_PASSWORD`：単一閲覧者のログイン。テスト値を本番で使わない。
- `STUDIO_SESSION_SECRET`：32文字以上のランダム値。変更時に既存セッションは無効。

`NEXT_PUBLIC_`には秘密を一切設定しない。Next.js `.env.local`、FastAPI環境変数または運用者の秘密管理から渡す。ローカルOSの既存ログインを変更・流用していない。

FastAPIは`uvicorn app.studio_reader:app --host 127.0.0.1 --port 8135`、Next.jsは通常ビルド後`next start --hostname 127.0.0.1 --port 3135`。**今回のサービスはloopback限定**。アドレスを0.0.0.0へ変更して無断公開しない。

## 保全・復元

コピー開始前に本番JSONを非公開バックアップし、隔離領域で再読込・等価復元を確認する。元台帳へ戻す必要は通常ない（本MVPは書かない）。復元が必要になった場合は後続revisionの有無を確認し、現行版を保全したうえで別承認で行う。古いr35を無条件に上書き復元しない。

閲覧コピー更新は常に新しいディレクトリを作成し、照合完了後にSTUDIO_SNAPSHOT_DIRを切り替える。旧コピーを保持する。失敗した不完全コピーはmanifest未完成のため接続不可になる。

## 検証結果

- FastAPI／インポーター15件、署名セッション8件、ローカルHTTP結合27件PASS。
- Next.js 15.5.27のビルド・型チェックPASS。
- PC1280px、スマホ390pxで横はみ出しなし。原画拡大、版選択、タイムシート閲覧とEscape閉じ、実MP4の1倍速・5秒終端、参考候補3点の検索を確認。
- 別の隔離フロントエンドで接続失敗を再現し、未接続表示と再読み込みボタンを確認。
- 実データコピー最終版：元台帳71素材、EP00 r01〜r03の原画24枚・動画3本・資料、既存設定画／背景を含む85種類の私有ファイル。重複元を含む95件のコピー照合を確認。
- 元台帳revision35・全ID・41履歴・関連MASTER等13ファイルは前後同一。バックアップの隔離復元検証済み。
- 実データ、スクリーンショット、絶対パス入り照合レシート、認証情報は公開Gitに含めない。

## 既知の限界・次工程

- 実機スマートフォンからの外出先接続、本番運用、HTTPS経由の配信は未実施。スマホ幅のブラウザ検証と区別する。
- 本番公開前に、承認済みの認証基盤／複数ユーザー権限、共有レート制限、サーバー側セッション失効・監査ログ、HTTPS終端と信頼するプロキシ／正規Originの設定、非公開ストレージとバックアップ運用をレビューする。
- 現在の単一プロセス・グローバルログイン試行制限はローカルパイロット用。ログアウトはブラウザCookieを削除する。コピー済みCookieの個別失効・役割管理・MFAは未対応。公開可と評価しない。
- `/production`以外の旧Next.js画面や別稼働中の旧APIをインターネットへ公開する許可ではない。専用Reader以外のFastAPIを配信しない。
- Mac原本とWebコピーは自動同期しない。ライブrevisionではなく**取得時点のsource revision**。
- 素材の生成時権利・公開許可を再認定しない。未公開素材は検証環境の認証付き閲覧だけ。
- SNS運営・収益管理・承認書込み・PWA・通知・AIジョブ連携は未実装。架空の作業状況は表示しない。
- 既存ローカル原稿リーダー・編集機能への統合作業は未実施。今回の開発ブランチはGitHub版へ追加する閲覧モジュールで、本番3128の置き換えではない。

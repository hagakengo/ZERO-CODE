# ZCS-OS-018｜Studio Memory v0.1 隔離先行運用マニュアル

状態：DRAFT。**隔離コピーと合成データだけ**に適用する。元保管庫、本番OS、実鍵、正式登録、外部公開には適用しない。正式運用は[完成判定](ZCS-OS-018_READINESS_DRAFT.md)でFAIL／開始不可。

## 担当と承認境界

Work 02は制作前参照と原文付きDRAFT提出、Work 01はReader／提出サービスの停止・起動、資格情報の発行・失効、出典照合、ブリーフ・監査・バックアップを担当する。監督AIは内容を評価して`REVIEW_PASS`／`REVIEW_REWORK`／`REVIEW_HOLD`を**提案**する。director技術署名者とプロデューサーの署名は、それぞれ指定された人間が審査票を確認して行う将来工程である。AIレビューのみでは`DIRECTOR_REVIEWED`にならない。現在は実鍵と正式登録を使用しない。

## 起動前の確認

1. 対象の保管庫、Reader認証、提出root、DRAFT候補庫、workflow rootを**明示的に指定**する。元保管庫や本番OSへ接続しない。コピーのノートSHA、候補ID・状態、保存先の所有者と権限を記録する。
2. コピー保管庫と秘密rootを`0700`、ノート・資格情報を`0600`にする。シンボリックリンク、未知のファイル、元資料と異なるハッシュがあれば起動しない。同一macOSユーザーのWork間を強く隔離できたとは扱わない。
3. `backend/.venv-reader/bin/python`のPython 3.12環境を使用する。Readerの認証rootと提出rootは別にする。既存の`ZCS-OS-016_RUNBOOK_DRAFT.md`の`recover`→`check`で不完全な受付を検出し、解消前は提出サービスを起動しない。
4. Readerは認証済み・ループバックのみ、アクセスログを無効化して起動する。提出サービスは`python -m tools.memory_submission serve --root <隔離提出root> --port <隔離port>`で127.0.0.1にのみバインドする。外部公開用URL・トンネルを使わない。実行PID、開始時刻、対象rootを私有運用記録へ残す。

## 通常の制作前参照

1. Work 01が`python -m tools.memory_auth --auth-dir <隔離Reader認証root> issue --work work02 --access all --ttl 300 --out <私有tokenファイル>`を実行する。Work 01自身の資格情報は`--work work01 --access approved`とし、Work 02用と混ぜない。token本文をチャットやログへ貼らない。
2. Work 02は対象エピソード・人物・素材で認証済みReaderを検索し、詳細の`memory_id`、`approval_status`、`approval_scope`、`sources`、`related`、`updated_at`を確認する。検索失敗は「記憶なし」と報告しない。
3. `python -m tools.memory_brief --url http://127.0.0.1:<Reader port> --token-file <私有tokenファイル> --target <対象> --query <検索語> --out <私有出力.md>`で制作開始ブリーフを作る。出力はMarkdownとJSON、両方とも私有領域に保存する。`APPROVED`も制作対象への適用範囲を別途確認する。DRAFTは参考。
4. 監督用には、出典SHAと候補状態を確認した既存DRAFTレビューpacketを用いる。`python -m tools.memory_review_brief --start-json <制作開始.json> --start-sha256 <SHA> --review-packet <packet.json> --packet-sha256 <SHA> --out <私有監督用.md>`。技術QC、演出・作画QC、監督評価、MASTER、公開、正式記憶登録を別々に読む。監督の内容評価を人間署名と混同しない。

## DRAFT提出・監督レビュー

Work 02は完了報告の原文、出典SHA、完全一致する判断・理由抜粋、未確認事項を用意する。Work 01は提出専用の短命資格情報を`python -m tools.memory_submission issue --root <隔離提出root> --out <私有tokenファイル> --ttl 300`で発行する。`submit`にはReader用tokenを渡さない。送信が途中で失敗した場合は**同一受付ID・同一内容**で再送する。受付IDのみを再利用して内容を変えない。

Work 01は`receipts`、`receipt`、`check`、`packet`で受付・原文SHA・候補DRAFT・承認範囲を確認する。原文抜粋、出典ハッシュ、記憶ID重複、関連記憶の範囲に疑義があれば`NEEDS_CORRECTION`または`REVIEW_HOLD`のまま止める。監督用パケットは私有領域に保管する。今回の隔離先行利用ではproducer署名と`register`を実行しない。

## 監査と停止

Reader監査は時刻、Work識別子、検索／詳細、HTTP結果だけ。提出監査は時刻、提出元、操作、結果、受付IDだけを扱う。本文、token、検索語、秘密鍵を監査・作業報告へ写さない。Work 01が異常な拒否・受付不一致・監査保存失敗を確認し、必要なら対象Work資格情報を失効する。停止時はReader・提出サービスのプロセスを終了し、短命資格情報を失効して私有tokenファイルを安全に除去する。DRAFT候補と監査・履歴は削除しない。

**即時停止条件：** 出典SHA不一致、受付と候補の不整合、DRAFTの予期しない昇格、署名対象改変、鍵台帳／監査不一致、資格情報漏えい疑い、バックアップ破損または旧世代混入、サービスの外部公開疑い。原因を解消するまで自動再起動・正式登録・公開を行わない。

## バックアップ・障害復旧

全writerを停止してから、既存`tools.memory_backup`で提出・DRAFT・vault・workflow・Reader認証の5つを一体snapshotにする。`verify`で各ハッシュ、ファイル一覧、sequenceを確認する。Readerと提出のサービス署名秘密はsnapshot対象から除外される。実運用でのsnapshot保管先と独立anchorはまだ未承認なので、現時点では**合成・隔離試験のみ**。

障害後は`tools.memory_submission recover`、続いて`check`を実行する。受付の欠落・競合・破損は証拠を残して停止し、手動でAPPROVEDへ変更しない。署名登録の復旧は合成候補でだけ検証済み。詳細は[ZCS-OS-016復旧手順](ZCS-OS-016_RUNBOOK_DRAFT.md)を参照する。

復元は停止した隔離環境の**新規パス**へ行い、旧パスを上書きしない。snapshotを検証し、保護されたanchorの最新世代より古ければ拒否する。復元後はすぐ起動せず、絶対パス設定を新しい私有rootへ再結線し、出典SHA・候補DRAFT・承認範囲・監査・公開鍵台帳・署名証拠を照合する。Readerと提出の新しい署名鍵を別々に作り、旧tokenが拒否されることを確認してから資格情報を再発行する。旧資格情報を同じ鍵と一緒に戻してはいけない。producer秘密鍵は本snapshotから復元しない。復元時間は未測定で、手動の再結線と確認が残る。

## 正式運用に切り替える前の確認

プロデューサーが別OSユーザーなどの所有主体、director技術署名者、producer鍵のオフライン保全、元保管庫の移設／権限、独立anchorの保管者、復元訓練を承認する。その後、Workから鍵の読取・署名が拒否されること、Reader tokenで提出できないこと、提出tokenで登録できないこと、失効済みtokenが復元後も拒否されることを**別主体で実測**する。PR #8〜#15は順序とロールバックをレビューした上で別途統合判断する。正式運用の開始は、これらの実測とプロデューサーの明示承認まで行わない。

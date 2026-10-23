# ZCS-OS-019｜PR統合承認チェックリスト・プロデューサー4ゲート

状態：**DRAFT／統合準備のみ**。2026-10-24時点。PR #8〜#16は変更・マージせず、main・本番OS・公開環境にも反映していない。

## PRの実在・依存順・変更領域

GitHubのbase/head、Draft状態、merge state、CIを再取得した。9件はいずれも**Draft／CLEAN／backendとfrontendのCIがSUCCESS**。この結果は各PRの現行headに対するCIであり、mainへ連続マージした結果ではない。

| 順 | PR | base → head | 主な差分・重複注意点 |
| --- | --- | --- | --- |
| 1 | #8 | `main` → `feat/os-production-readonly-mvp` | 認証付き制作閲覧MVP、Reader／Web。#9もReader・BFF routeを編集。 |
| 2 | #9 | #8 head → `feat/studio-memory-v01` | Studio Memory Reader・Work別認証の基礎。 |
| 3 | #10 | #9 head → `feat/studio-memory-workflow-v01` | DRAFT候補、署名付き承認・登録の別管理経路。 |
| 4 | #11 | #10 head → `feat/studio-memory-approver-security-v01` | 公開鍵台帳・失効・審査票。#10と`memory_workflow.py`を共有。 |
| 5 | #12 | #11 head → `feat/studio-memory-draft-intake-v01` | DRAFT一覧・レビューpacket。`memory_workflow.py`を共有。 |
| 6 | #13 | #12 head → `feat/studio-memory-work-submission-v01` | Work間の提出専用経路。 |
| 7 | #14 | #13 head → `feat/studio-memory-recovery-v01` | 障害復旧・snapshot。workflow、DRAFT、提出コードを共有。 |
| 8 | #15 | #14 head → `feat/studio-memory-production-brief-v01` | 制作開始・監督レビューブリーフ。 |
| 9 | #16 | #15 head → `feat/studio-memory-v01-readiness-v01` | 完成判定、隔離運用手順、復元後の旧token拒否テスト。 |

想定と実際の依存順に差異はない。変更領域の重なりはstack内の連続編集であり、**競合が存在しないと実マージで立証したわけではない**。各head SHAを統合時に再取得・固定する。#8/#9のReaderとBFF、#10/#11/#12/#14のworkflow、#12/#13/#14のDRAFT・提出が重点レビュー箇所。現在の先端でReader書込APIなし、DRAFTと`approval_status`の区別、AIレビューと人間署名の区別、SNS承認とMASTER承認の区別を回帰テストで確認した。

追跡対象のGitファイルを、秘密鍵PEM・典型的なサービスtoken接頭辞・長い秘密代入値という3種の**限定的な正規表現**で検査し、候補0件。秘密らしい名前の追跡ファイルも0件。これはGitHub側のsecret scanningや履歴全体の保証ではない。マージ前には各PRの追加行、バイナリ、Git履歴、CIログを人間が再審査する。私有記憶本文、実資格情報、実鍵、元保管庫のコピーを公開Gitへ追加しない。

## ゲート1｜環境変更の承認（今回未実施）

producerが具体的な対象・担当・戻し方を確認して個別承認する事項：

1. producer専用標準macOSユーザーとReader／管理主体、Work 01・02の実行UID分離をどう構成するか。現在のWorkが`admin`である点、sudo、TCC、画面操作・自動化をどう制限するか。
2. 元の0755/0644保管庫を別所有者の新規領域へコピーして切り替えるか、または別案。親パス、ACL、symlink、Reader／CLIからの参照、原本保持を含む。
3. 人間のdirector技術署名者、producer秘密鍵の発行・保管・紛失時責任者。AIやWorkは署名しない。
4. snapshotとは別主体の最新sequence＋manifest SHA-256受領記録の場所・管理者・更新頻度。媒体や権限の作成を含む。

**ゲート1は環境変更だけ**を許可する。コードマージ、実記憶登録、正式運用開始は許可しない。承認がない間は移設、chmod/chown、ユーザー作成、実鍵発行を実行しない。

## ゲート2｜実環境の安全性検証（ゲート1後）

| 必須試験 | PASS基準 | 現状 |
| --- | --- | --- |
| Work→producer鍵・署名 | Work 01・02から読取／署名要求が拒否。producer本人セッションでは審査票の対象・差分を確認可能 | **未実施**。同一UIDの合成署名テストは代替にならない |
| Work→元保管庫 | Workの直接読取・変更が拒否。Readerは承認済み範囲でだけ読める | **未実施**。隔離コピー0700/0600の同一プロセス試験のみ |
| 認証境界 | Reader tokenで提出不可、提出tokenで登録不可、失効済みtoken不可 | 合成テストPASS、別OS主体では**未実施** |
| backup巻き戻り | Workが保護受領記録を変更できず、旧・破損・未受領snapshotを拒否 | **未実施**。同一UIDのanchorは巻き戻せる |
| 復元・再起動 | 新規パスで出典・状態一致、旧token拒否、新token発行、監査と停止条件確認 | 合成データの単体試験のみ。別主体・実運用相当は**未実施** |

いずれかがFAILならゲート3・4へ進めない。別主体の実試験を行う承認は、ゲート1の構成と環境変更の承認範囲を確認した後に得る。

## ゲート3｜コード統合の承認（今回未実施）

1. #8〜#16のbase/head SHAと差分を固定。privateデータと秘密の混入を再検査。すべてDraftのまま最終レビューを行う。
2. mainの新しい隔離コピーで**#8から#16へ順番に**差分を適用し、各段でbackend・frontend・承認範囲・Reader/提出境界・データ形式を確認。前段を飛ばしてbaseをmainへ付け替えない。
3. 隔離統合結果とCIが緑でも、本番OS・MASTER・実記憶のハッシュと復旧手順を再照合し、producerに**mainへの各段マージ可否**を別判断してもらう。
4. マージ後も実運用接続・実鍵使用・正式登録はゲート4まで行わない。

現時点のローカルbackend 138件、frontend 9件、TypeScript、Next.jsビルドはPASS。GitHubの既存PR #8〜#16のCIもbackend/frontend SUCCESS。ただし**今回mainへ適用した統合試験は実施していない**。Stacked PRの`CLEAN`は各baseとの状態であり、将来のmainとの衝突やデータ移行の安全性を保証しない。

**ロールバック：** 将来のマージ前にmainと各headのSHA、本番OS・候補・元記憶のSHA、私有snapshotと独立受領記録を固定する。障害時はReader／提出／登録を停止し、影響したマージを逆順にrevertして隔離環境で全テストを実施する。DRAFT、監査、署名履歴は削除しない。実データの復元が必要なら新規パスへ復元し、出典と承認状態を照合して資格情報を再発行する。今回の禁止範囲のため、mainの実マージ／実ロールバックは未実施。

## ゲート4｜正式運用開始の承認（今回未実施）

producerがゲート2の証拠、ゲート3の統合結果、運用当番・停止条件・鍵紛失／復元手順を確認したうえで、**実制作記憶への接続、実運用Reader・提出、人間の正式署名・登録**を別々に承認する。開始後もDRAFTを自動APPROVEDにしない。`YUNA-EYE-001`と`WORK02-EP00-R03-001`は別IDのまま、技術QC PASS、演出・作画QC REWORK、監督内容レビューREVIEW_HOLD推奨、MASTER／公開／正式記憶登録は未承認。今回の承認ゲート資料はその状態を変えない。

## 現在許される制作利用

隔離コピーのReaderを127.0.0.1限定・短命のWork別tokenで使い、制作開始／監督用ブリーフを参照する。DRAFTとAPPROVEDおよびAPPROVEDの**承認範囲**を毎回確認する。実制作記憶は登録せず、制作素材・MASTER・公開承認を変更しない。試験後はtokenを失効させサービスを停止する。ZCS-OS-017のWork 02独立接続は過去の実証であり、本工程で新しい独立Work 02試験は行っていない。

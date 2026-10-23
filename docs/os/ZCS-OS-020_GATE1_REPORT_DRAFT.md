# ZCS-OS-020｜ゲート1環境整備報告

2026-10-24 JST／**DRAFT・監督レビュー用**。ゲート1の方針に沿う手順と合成照合試験を用意した。**専用OSユーザーの作成、実データの移動、権限変更、実鍵発行、producer保護領域の作成は未実施**。したがって環境分離そのものは未完成で、ゲート2の実拒否試験も未実施。正式運用判定は引き続き**開始不可**。

## 提出物と証拠

| 指示書の項目 | 提出先・結果 |
| --- | --- |
| 変更前環境、macOS主体、元庫・OS・候補の保全 | [ゲート1環境整備記録](ZCS-OS-020_GATE1_ENVIRONMENT_DRAFT.md)。UID 501がadmin所属、元庫0755／3件0644、元記憶のsymlink 0。前後5ファイルのSHA一致 |
| 専用ユーザー構成、人間向け作成手順、元庫コピー、停止・撤回 | [ゲート1環境整備記録](ZCS-OS-020_GATE1_ENVIRONMENT_DRAFT.md)。個別承認後に本人が操作する段階で停止 |
| director/producer署名と鍵紛失対応 | [署名・backup受領設計](ZCS-OS-020_SIGNING_BACKUP_DRAFT.md)。秘密鍵の実発行・技術署名なし |
| 独立backup受領形式・照合・復元停止 | [署名・backup受領設計](ZCS-OS-020_SIGNING_BACKUP_DRAFT.md)。現行CLIには自動ゲート未実装。人間の別主体確認が正式運用前提 |
| ゲート2拒否・復元試験 | [ゲート2計画](ZCS-OS-020_GATE2_PLAN_DRAFT.md)。G2-01〜07はいずれも別主体で未実施 |
| 合成試験 | [合成受領照合テスト](../../backend/test_memory_gate1_witness.py)4件PASS。最新受領一致、作業anchor巻き戻し下の旧版拒否、破損拒否、受領欠落／未受領拒否 |
| テスト | backend `unittest discover` 142件PASS。frontend `test:studio` 9件PASS、`npx tsc --noEmit` PASS、`npm run build` PASS。最初に汎用`npm test`/`npm run typecheck`を試したが、このrepoにスクリプトがなく不実行。正しいコマンドで再実施した |
| CI／PR | 既存PR #8〜#17はDraft。作業開始時#17のbackend/frontend CI PASS。新規Draft PRのCIは作成後の結果を別途記録する |

## 状態・範囲の再確認

`YUNA-EYE-001`はDRAFT。`WORK02-EP00-R03-001`もDRAFTで、技術QC PASS・演出/作画QC REWORK・監督内容レビューはREVIEW_HOLD推奨のみ。本編MASTER・公開・正式記憶登録は未承認。`K07-PUBLICATION-001`の承認はX02へのSNS公開範囲に限り、本編MASTERを意味しない。この工程はこれらのファイルも本番OSも変更していない。

## 残る重大条件

1. 現在のWorkはadminかつ元記憶庫と同じUID。専用標準ユーザーを追加しただけでは、Workからのadmin/TCC/GUI越境と旧庫の直接読取が解消されたとはいえない。旧庫を保持したままどう読取権限を制御するか、producerの個別判断が必要。
2. producer秘密鍵、別人のdirector技術署名者、producer管理の受領記録は未設定。実鍵での署名拒否・別主体の受領記録変更拒否は未実測。
3. 現行backup CLIは独立受領記録を自動照合しない。照合手順は合成テストで検証したが、正式復元の技術的ゲートではない。受領失敗、受領記録紛失時は手動停止。
4. TCC/Automation・Reader/受付/管理CLIの本番実行主体と、恒常的snapshot/anchor場所は未照合。別所有者rootでの管理CLI運用は未検証。

## 次の判断

プロデューサーに求めるのは、[ゲート1記録の個別判断待ち一覧](ZCS-OS-020_GATE1_ENVIRONMENT_DRAFT.md)から**具体的な操作ごとの承認**である。特に、専用標準ユーザーを誰がどう作るか、Workのadmin/TCC境界をどう制限するか、旧庫と新庫の所有者・パス・ACL、別人director署名者、producer鍵・受領記録の保管方式を先に確定する。承認後にだけゲート2の別主体拒否・復元試験を行う。PR #8〜#17のマージ、本番Reader切替、正式登録、正式運用開始は別ゲートの判断とする。

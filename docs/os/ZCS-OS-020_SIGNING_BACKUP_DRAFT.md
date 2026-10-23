# ZCS-OS-020｜人間署名・独立バックアップ受領記録

状態：**DRAFT／合成試験のみ**。実署名鍵、producer保護領域、実制作記憶の正式登録は未実施。

## 人間承認の分離

AI監督は内容評価 `REVIEW_PASS / REWORK / HOLD` を提案するだけ。別の人間director技術署名者は記憶ID、原文SHA、出典、差分、承認範囲、署名鍵ID、有効期限、nonceを審査票で確認し、本人の秘密鍵で`DIRECTOR_REVIEWED`に署名する。producerは同じ対象を本人の専用セッションで再確認してから最終署名する。Workに秘密鍵を渡さず、Workが署名の確認クリックやパスワード入力を代行しない。directorとproducerが同一人なら二者独立性は成立せず、別人の技術署名者を指定するか運用を止めて再設計する。

既存`memory_workflow`のEd25519公開鍵台帳・失効・nonce・署名順序検証を再利用する。審査票の本文やscopeを変更したら旧署名は破棄し、新しい審査票を発行する。鍵発行と保管方式（別macOSユーザー内のOS保護、別端末／ハードウェア等）はproducerが個別に選ぶ。単なる同一UIDの別フォルダーは秘密鍵隔離ではない。秘密鍵の紛失・漏えい疑い時は新規署名・登録を停止し、公開鍵IDと有効期間、署名済み審査票、監査を保全する。漏えい鍵を失効し、別の信頼経路で再発行・台帳更新するまで再開しない。紛失時もAI/Workが代行して復旧しない。実鍵のバックアップ・復元は本工程の対象外。

## 二層のバックアップ基準

作業用anchorは既存の`anchor/state.json`のまま。独立受領記録はproducer管理主体が**成功したsnapshotの検証後**にのみ受け取る。作業側が受領記録を直接書けてはならない。受領が失敗・遅延したsnapshotは未受領として復元不可。次回snapshotでsequenceだけ進めても未受領を自動承認しない。

提案する受領記録の最小形式（非秘密メタデータだが保護対象）：

```json
{
  "version": 1,
  "snapshot_id": "snapshot-<opaque-id>",
  "sequence": 2,
  "manifest_sha256": "<64 lowercase hex digits>",
  "received_at": "<producer-side timestamp>",
  "receiver": "<human-controlled principal identifier>"
}
```

`manifest_sha256`は確定snapshot内の`manifest.json`**実バイト列**をSHA-256で計算する。`snapshot_id`は単なる表示名ではなく、受領側が実際に確認した保存物と照合する。`sequence`は正の整数で、直近の受領より厳密に増加させる。`received_at`と`receiver`はproducer側が記録し、Work側の申告値を無検証で採用しない。受領内容にsnapshot本体や秘密鍵を含めない。受領履歴は追記型で保管し、最新レコードだけを検証基準とする。保存先の具体的パスと保護方式は個別承認待ち。

手順：writer停止 → 既存backupを私有領域に確定 → `verify_snapshot`による全ファイルとmanifest検証 → `sequence`と`manifest` SHAを独立受領者へ安全に提示 → 受領者が保存物を直接確認し、前回より新しいことを確かめて記録 → 受領成功を作業側に返す。復元時は**独立受領者の最新レコードを先に取得**し、対象snapshotのID、sequence、manifest実バイトSHA、全ファイルのhashを突合する。旧・破損・未受領snapshotまたは受領記録欠落は拒否。復元は必ず新規パス、資格情報は別々に再発行し、旧資格情報の拒否を確認する。詳細は[既存復旧手順](ZCS-OS-016_RUNBOOK_DRAFT.md)。

旧sequenceへ作業用anchorが巻き戻されても、独立受領記録の最新sequenceと一致しなければ拒否する。ただし、同じUIDのWorkが受領記録も書き換えられる場合は**独立保護PASSではない**。producer側の保護領域を作成するまで、これを技術的な巻き戻り防止と主張しない。受領記録紛失・破損時は自動復元を停止し、producerが別保全証拠と監査をもとに再構築可否を判断する。曖昧な場合は復元しない。

## 合成試験の意味と限界

`backend/test_memory_gate1_witness.py`は既存`memory_backup`で合成DRAFTノートを含む2世代のsnapshotを作り、最新受領に一致したsnapshotを受理し、作業用anchorを巻き戻しても旧snapshotを拒否し、破損・受領欠落・未受領を拒否する。これは**照合ルールの隔離試験**であり、別OS主体による受領記録の変更拒否も、実復元にゲートが組み込まれたことも証明しない。現行CLIの`restore`は独立受領記録を自動参照しないため、正式運用前に人間の受領照合を必須手順として固定し、ゲート2で実際の保護・拒否を測る。

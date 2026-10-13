# ZERO CODE｜監督レビュー提出：反撃→後退 動作設計案01

**DRAFT / 監督レビュー待ち。r15.2も正式判定待ち。**

## レビュー資料（ZIPの解凍不要）

- [新規案MP4](https://github.com/hagakengo/ZERO-CODE/blob/review/counterattack-design-01-20261013/reviews/counterattack_design_01/video/counterattack_retreat_design_24fps.mp4)：反撃→後退。P000〜P071、24fps、72フレーム、3秒、1080×1920、H.264 High Level 4.0 / yuv420p、音声なし。268,858 bytes。
- [キー姿勢PNG](https://github.com/hagakengo/ZERO-CODE/blob/review/counterattack-design-01-20261013/reviews/counterattack_design_01/design_keyposes.png)：P000 / P012 / P020 / P024 / P025 / P036 / P046 / P060の8姿勢。開始、予備、加速、接触、圧縮、後退、踏み替え、回復を確認。358,849 bytes。
- [足運び比較PNG](https://github.com/hagakengo/ZERO-CODE/blob/review/counterattack-design-01-20261013/reviews/counterattack_design_01/comparison/footwork_before_after.png)：既存r15.1とr15.2のf226〜233を同一フレームで比較。450,937 bytes。
- [既存比較MP4](https://github.com/hagakengo/ZERO-CODE/blob/review/counterattack-design-01-20261013/reviews/counterattack_design_01/comparison/r15_1_vs_r15_2_24fps.mp4)：r15.1とr15.2のf226〜233、24fps、8フレーム、約0.333秒、2160×1920、H.264 High Level 5.0 / yuv420p、音声なし。138,706 bytes。
- [元ZIP](https://github.com/hagakengo/ZERO-CODE/blob/review/counterattack-design-01-20261013/reviews/counterattack_design_01/ZERO_CODE_counterattack_design_01_review.zip)：元提出物13ファイルをそのまま保持。1,229,257 bytes。
- [今回の検証結果](https://github.com/hagakengo/ZERO-CODE/blob/review/counterattack-design-01-20261013/reviews/counterattack_design_01/verification/submission_checks.json)：容量、SHA-256、ZIP内ファイルとのバイト一致、動画の仕様・全フレームデコード結果。

## 確認方法・フレーム番号

1. 新規案MP4を開く。GitHubで再生できなければRaw／Downloadから保存し、H.264対応プレイヤーで通常速度・コマ送り確認する。
2. P020〜025の加速と初接触（P024）、圧縮（P025）、P026〜035の反応、P036〜055の後退、P042〜050の踏み替えを確認。P番号は新規案専用の0始まりで、時刻はP番号÷24秒。r15.2のf番号へ割り当てない。
3. キー姿勢PNGを拡大確認する。新規案には同時点の旧版がなく、キー姿勢一覧を同一フレームの修正前後比較とは扱わない。
4. 既存比較PNGと比較MP4でr15.2のf226〜233を別途判定する。比較動画の末尾→冒頭は動作接続の判定から除く。
5. 詳細設計・品質チェック・従来の検証・再現コードはZIP内を参照。ZIP内報告の「ZIP1つ」「Git pushなし」は元提出時点の記録であり、今回の提出状態は本READMEを参照する。

## 検証・保全（2026-10-13 JST）

- 単独動画2本とPNG2枚はZIP内と同一バイト。再圧縮・再描画・編集なし。
- ffprobeで両動画のH.264・24/1fps・フレーム数・尺・容量を実測。ffmpegで全フレームをエラーなしでデコード（PASS）。
- GitHub内蔵プレイヤーと個々の端末での再生は未検証。特に比較動画はLevel 5.0のため、再生できない端末ではPNGで確認する。技術検証は演出の監督PASSを意味しない。
- 元ZIP SHA-256：`26f9d88a545e3e5955785f9a7640ebfb9a8e2a382e98297309fa47e1e0effedb`（変更なし）。
- 今回の変更はこのレビュー用フォルダ内のみ。既存素材・main・r15.2 f226〜233は変更しない。公開・課金・本番反映なし。
- 監督のPASS／修正指示を待つ。承認前にMASTER昇格・既存素材への統合・次工程へ進めない。

以後の提出には[レビュー提出標準ルール](REVIEW_SUBMISSION_STANDARD.md)を適用する。

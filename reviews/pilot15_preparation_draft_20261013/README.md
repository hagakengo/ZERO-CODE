# ZERO CODE 15秒パイロット 制作準備 DRAFT

2026-10-13 JST / 全成果物DRAFT / レビュー専用・未承認。映像本編・完成音源ではない。

**案04は監督HOLD継続。通常速度の演出判定は未確定。** 本提出はブロッカーから独立した設計・検査準備のみ。案05制作、案04の15秒本編への組込み、MASTER昇格、公開、投稿、本番反映は実施しない。

## 確認順序・成果物

1. [出典と承認状態](SOURCES_AND_STATUS.md)：GitHub資料とMac内v01/v02の来歴、未確認事項。
2. [ショット・ビート設計](TIMELINE_DRAFT.md) / [フレーム編集用CSV](timeline_draft.csv)：9:16、15秒、24fps、360fの提案。既存正式決定を上書きしない。
3. [音響キューシート](SOUND_CUES_DRAFT.md) / [キューCSV](sound_cues_draft.csv)：無音版から独立した準備。音源の取得・合成・流用・ミックスは未実施。
4. [整合性チェックリスト](CONTINUITY_CHECKLIST_DRAFT.md)：チェック未完了を合格に変えない。
5. [再判定後の分岐・再レビュー](NEXT_STEPS_DRAFT.md)：PASS、HOLD、視認不足を分離。
6. [安全な技術検査](source/inspect_media.py) / [設計検査](source/check_plan.py) / [実測結果](verification/source_media_checks.json) / [検証記録](verification/preparation_checks.json)。
7. [制作ログ](PRODUCTION_LOG_DRAFT.md)。全資料ZIPは本フォルダ直下の `ZERO_CODE_pilot15_preparation_DRAFT.zip`。ZIP外にも全個別資料を配置。

## 番号と実行

タイムラインは新規のF000〜F359、終端F360は含まない。CSVはstart_frameを含みend_frame_exclusiveを含まない半開区間。時刻=F/24秒。案04のP000〜071、r15.2のf226〜233と別体系。P→F割当は未実施。

リポジトリルートから実行：

```sh
python3 reviews/pilot15_preparation_draft_20261013/source/check_plan.py
python3 reviews/pilot15_preparation_draft_20261013/source/inspect_media.py --profile design04 reviews/counterattack_design_04/video/counterattack_design_04_24fps.mp4
# 将来の試験統合物用（今回は生成していない）
python3 reviews/pilot15_preparation_draft_20261013/source/inspect_media.py --profile pilot-silent /path/to/review-only.mp4
```

Python標準ライブラリとffprobe/ffmpegが必要。結果は標準出力のみ、入力は読み取り専用。技術PASSは指定数値・デコードの合格だけで、映像演出・権利・聴感・承認を保証しない。失敗は非ゼロ終了。

本提出は資料・スクリプトのレビューであり、新規映像修正版の提出ではないため、映像提出標準の新規MP4/主要PNGは対象なし。既存MP4は再圧縮・コピーせず出典リンクで参照。新規ZIPは準備資料を収録し、既存案01〜04のZIPは保持。

## 制約

v01/v02はMac内原本と制作報告を読取り確認、技術実測・全尺デコード済み。連続再生の演出レビュー・音声聴感レビューは今回未実施。GitHubの全取得ブランチ履歴のファイル名からpilot/v01/v02を探索したが原本を確認できず、未登録と断定はしない。D1の既存方向選定と本パイロットへの採用未決定を区別する。敵正式デザイン、HUD文言、CUT01原本、音源権利は未確認または未決定のまま。

mainおよび基準コミット57215e29の既存全追跡ファイルは不変。ローカルv01/v02、r15.2も読取り対象のみ。既存台帳・アプリ・本番環境の変更なし。

追加の検査制約：案04のピクセル縦横比メタデータは明示されていない。旧素材用検査では警告として保存し、画素寸法9:16と表示比率の保証を区別。将来の新規pilot用プロファイルは明示1:1を要求する。

# EP00 Yuna｜基準画像原本の再発見と局所演技TEST v02

**Date:** 2026-10-22  
**Status:** TEST / NOT MASTER / OS NOT SYNCED / NO PUBLICATION  
**Director verdict:** 技術検証PASS、演技品質REWORK

## 基準画像の実体確認
- 会話内ファイル `a_detailed_anime_studio_style_production_layout_po.png` を取得・目視確認。
- メタデータ上の生成ID `08ea6239-f852-4e01-a405-15184a5dc7b3` が、プロデューサー承認の画風基準 `ZCS-VISUAL-001 v1.0` に記録されたIDと一致。
- 元画像：1024×1536 PNG、2,370,767 bytes、SHA-256 `73a5b21314bb87219948da2f03b48a019d441b35f9ab28c84041ab4747d9fee6`。
- 最下段「完成イメージ」から既存切り出し `ep00_final_panel_crop.png` を確認：1024×371 PNG、584,432 bytes、SHA-256 `e033bea4d0e63a1d0c9e9ceca28905ee46249c95963c118d456bb7eb22be1cf3`。
- このセッションの作業領域 `/mnt/data` に存在し、ユーザーにダウンロード可能な制作パッケージとして提供。**Mac制作フォルダやZERO CODE OSへの永続保管は未確認。** GitHubに画像・動画バイナリは追加していない。
- 元画像は映画的な画風の**目標参照**。正式ユナの人物MASTERではない。BG-A/BG-A2との照合と公開権利の確認は別工程。

## 実制作：局所演技TEST v02
- 画像の顔・カフェ・窓枠・カップを原則固定したまま、瞳周辺を最大約2.2px局所変位、口角を最大約1.4px局所変位。窓側の一つの雨粒を追加で移動。
- 24fps×5秒=120フレーム、無音、H.264。Python/OpenCVの局所ワープとFFmpegによるローカル書き出し。外部動画生成AIへの有料生成はなし。
- `EP00_YUNA_ACTING_TEST_v02_wide.mp4`: 1024×576（横構図レビュー用）、119,192 bytes、SHA-256 `1af1eb0dea2639609c3e529159fbe94aadb7d1acfafeb4632cc24b2b8bff359c`。
- `EP00_YUNA_ACTING_TEST_v02_portrait.mp4`: 720×1280（縦構図技術プレビュー）、124,519 bytes、SHA-256 `8e649e89d9215c1e6e9cbfcebc8c3d7a204aa1226de9e1dc212c0d6baac3b3e5`。
- `EP00_YUNA_ACTING_TEST_v02_contact.jpg`: F000/F048/F110の確認用画像。
- `make_ep00_yuna_acting_v02.py` と `EP00_YUNA_ACTING_TEST_v02_QC.json` を作業領域に保存。ZIP `ZERO_CODE_EP00_YUNA_VISUAL_TEST_v02_package.zip` に同梱。
- ZIP SHA-256 `7a470b5c38042e657f3c4a59425a5d0b785cf7b81d65ea941fe73eafb356cd4e`。

## QC
| 項目 | 結果 |
|---|---|
| 基準画像生成ID一致 | PASS（画像メタデータを照合） |
| 出力尺・24fps・120フレーム・縦解像度 | PASS（ffprobe実測） |
| 眼と口の局所画素変化 | PASS（F048の眼領域1168画素、F110の口領域297画素がF000から変化） |
| 目線が雨粒を自然に追うか | REWORK（変化量が小さく、演技として読める保証なし） |
| 笑顔の説得力 | REWORK（口角ワープのみ。正式な差分原画ではない） |
| 9:16の完成構図 | REWORK（横長原画の中央クロップと上下ぼかし延長。完成画ではない） |
| 同一キャラの正式参照整合 | UNVERIFIED（BG-A/BG-A2/ユナ正式原画未照合） |
| 目視・実時間通し視聴、音声 | 3フレーム静止確認のみ／実時間視聴未実施／無音 |
| 公開権利・MASTER昇格 | UNVERIFIED／実施しない |

**結論:** v01で未実装だった瞳・口角の局所的な時間変化を実装したが、まだ自然な演技を十分に表現したアニメとは言えない。映画的な画風は保全しつつ、正式な表情差分原画が必要。再生しても「AI感が消えた」と断定しない。

## 次
1. 基準画像の原本をMacの制作資産保管先にコピーし、SHA-256一致を確認。
2. 公式ユナ/BG-A/BG-A2を実物照合。既存承認済み脚本・キャラ設定を優先。
3. 同一構図の目・まぶた・口角の差分原画P0/P1/P2を描き直し、より読める演技にする。
4. 縦画面の**完成構図を原画段階から設計**する。上下ぼかし延長を最終演出に使わない。
5. 動画生成AIとのA/B比較は、参照・権利・コスト確認後に行う。未実施のまま勝敗を決めない。

**Protection:** 既存68資産ID・状態・履歴、MASTER、脚本、OS本番データ、公開設定に変更なし。

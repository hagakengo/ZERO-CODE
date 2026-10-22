# EP00 Asset Intake｜再利用素材の照合台帳 r01

**Status:** DRAFT / 文書上の登録のみ / 実ファイル未検証 / OS未同期  
**Date:** 2026-10-22  
**Scope:** 正式採用小説版EP00『正しい世界』の第05節・雨のカフェ。旧「¥0」プロトタイプとは区別。

## 素材登録（推定で空欄を埋めない）

| Asset ID | 種別 | 既存の呼称・参照 | 既知の用途 | 実ファイル取得 | SHA-256実測 | 権利照合 | この制作での状態 |
|---|---|---|---|---|---|---|---|
| EP00-BGA | 背景・引き画 | BG-A / `BG-A_scene_panel_approved_reference.png` | 三階カフェ全景 | 未取得 | 未計測 | 未確認 | REFERENCE-PENDING |
| EP00-BGA2 | 背景・人物寄り | BG-A2 / `BG-A2_Yuna_rain_window_closeup_3F_approved.png` | 雨窓とユナの横顔 | 未取得 | 未計測 | 未確認 | REFERENCE-PENDING |
| EP00-YUNA-REF | キャラクター参照 | ユナの既存承認参照（正式ファイル名未確認） | 顔・髪・瞳・衣装の一致 | 未取得 | 未計測 | 未確認 | REFERENCE-PENDING |
| EP00-YUNA-P0 | ポーズ絵 | 5秒ショットP0 | 雨粒を見る | 未制作 | — | — | DRAFT-SPEC |
| EP00-YUNA-P1 | ポーズ絵 | 5秒ショットP1 | 視線追従 | 未制作 | — | — | DRAFT-SPEC |
| EP00-YUNA-P2 | ポーズ絵 | 5秒ショットP2 | 小さな笑み | 未制作 | — | — | DRAFT-SPEC |
| TEASER-KLING-C | 動画テスト | 雨のカフェKling TEST | 構図・照明の参考候補 | 今回未取得 | 今回未計測 | 未確認 | TEST-REFERENCE-ONLY |

※BG-A/BG-A2の「承認済み」は過去の挿絵配置レビュー内の表現。実物・承認証拠・動画MASTER化・商用公開可否は別問題。今回GitHubへの画像バイナリの追加は行っていない。

## 受け入れ基準
1. 元ファイルをコピーで保全し、オリジナルを上書きしない。
2. SHA-256、ピクセル寸法、縦横比、色空間、作成元、モデル、生成日時（判明時）、保存場所、権利根拠を登録。
3. 素材IDと版を固定し、同一人物・背景の派生を `P0/P1/P2` のように追跡する。
4. `REFERENCE-PENDING → TEST → CANDIDATE → APPROVED` は別の審査。既存MASTERの指定があれば明示的承認を要する。
5. 商用利用・透かしの許諾が未確認なら公開に使わない。加工で透かしを消すことを権利解決と扱わない。
6. 作品本文・正史・承認済みMASTERはこの台帳によって変更しない。

## 取得元候補（過去の配置レビューに記載、存在を再確認していない）
- EP00 v08挿絵配置レビュー r02 の相対参照: `assets/BG-A_scene_panel_approved_reference.png`
- 同: `assets/BG-A2_Yuna_rain_window_closeup_3F_approved.png`
- 採用本文原本の制作記録上のパス: `/Users/hagakengo/Movies/ZERO_CODE/production/ZERO_CODE/EP00/scripts/ZERO_CODE_EP00_正しい世界_v08_正式採用_20261020.md`
- 採用本文の制作記録上のSHA-256: `7fe56111940facec8588aa5ef8d317822eccb4257b0dce8f977103ee98ea2ab6`（この作業で再計算はしていない）

## 次の工程
BG-A/BG-A2とユナの承認参照の実物取得 → ハッシュ・寸法・権利照合 → 3ポーズ制作 → 同一性レビュー → 動画方式選定。費用・外部公開・MASTER昇格は別承認。
